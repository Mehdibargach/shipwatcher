"""
Check engine — runs health checks and smoke tests against monitored projects.

Handles Render free tier quirks:
- Cold starts (30-60s): retry with longer timeout on first attempt
- Rate limiting (429): exponential backoff between retries
- Sequential checks with pauses to avoid triggering platform rate limits
"""

import asyncio
import time
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("shipwatcher.checker")

# Retry config
MAX_RETRIES = 3
RETRY_DELAYS = [15, 30, 60]  # seconds between retries
HEALTH_TIMEOUT = 90  # generous timeout for cold starts
SMOKE_TIMEOUT = 180
PAUSE_BETWEEN_PROJECTS = 3  # seconds between each project


@dataclass
class CheckResult:
    project_id: str
    project_name: str
    check_type: str  # "health" or "smoke"
    success: bool
    latency_ms: int = 0
    status_code: int = 0
    error: str = ""
    details: str = ""


def _should_retry(status_code: int = 0, is_timeout: bool = False) -> bool:
    """Decide if a failed check should be retried."""
    if is_timeout:
        return True
    # 429 = rate limited, 502/503/504 = service starting up
    return status_code in (429, 502, 503, 504)


async def run_health_check(client: httpx.AsyncClient, project: dict) -> CheckResult:
    url = project["url"] + project["health_endpoint"]
    method = project.get("health_method", "GET")

    for attempt in range(MAX_RETRIES + 1):
        start = time.monotonic()
        try:
            if method.upper() == "POST":
                resp = await client.post(url, timeout=HEALTH_TIMEOUT)
            else:
                resp = await client.get(url, timeout=HEALTH_TIMEOUT)

            latency = int((time.monotonic() - start) * 1000)

            if resp.status_code == 200:
                if attempt > 0:
                    logger.info(f"Health OK after {attempt} retries: {project['name']}")
                return CheckResult(
                    project_id=project["id"],
                    project_name=project["name"],
                    check_type="health",
                    success=True,
                    latency_ms=latency,
                    status_code=resp.status_code,
                )

            # Non-200 — retry if retryable
            if attempt < MAX_RETRIES and _should_retry(status_code=resp.status_code):
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Health {project['name']}: HTTP {resp.status_code}, retry in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                continue

            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="health",
                success=False,
                latency_ms=latency,
                status_code=resp.status_code,
                error=f"HTTP {resp.status_code}",
            )

        except httpx.TimeoutException:
            latency = int((time.monotonic() - start) * 1000)
            if attempt < MAX_RETRIES and _should_retry(is_timeout=True):
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Health {project['name']}: timeout, retry in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                continue

            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="health",
                success=False,
                latency_ms=latency,
                error=f"Timeout ({HEALTH_TIMEOUT}s) after {MAX_RETRIES} retries",
            )

        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="health",
                success=False,
                latency_ms=latency,
                error=str(e),
            )


async def run_smoke_test(client: httpx.AsyncClient, project: dict) -> CheckResult | None:
    """Run a functional smoke test. Returns None if no smoke test is configured."""
    if not project.get("smoke_endpoint"):
        return None

    url = project["url"] + project["smoke_endpoint"]
    payload = project.get("smoke_payload")
    payload_type = project.get("smoke_payload_type", "json")
    validate_field = project.get("smoke_validate_field")

    for attempt in range(MAX_RETRIES + 1):
        start = time.monotonic()
        try:
            if payload_type == "form":
                resp = await client.post(url, data=payload or {}, timeout=SMOKE_TIMEOUT)
            elif payload:
                resp = await client.post(url, json=payload, timeout=SMOKE_TIMEOUT)
            else:
                resp = await client.post(url, timeout=SMOKE_TIMEOUT)

            latency = int((time.monotonic() - start) * 1000)

            if resp.status_code != 200:
                if attempt < MAX_RETRIES and _should_retry(status_code=resp.status_code):
                    delay = RETRY_DELAYS[attempt]
                    logger.info(f"Smoke {project['name']}: HTTP {resp.status_code}, retry in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue

                return CheckResult(
                    project_id=project["id"],
                    project_name=project["name"],
                    check_type="smoke",
                    success=False,
                    latency_ms=latency,
                    status_code=resp.status_code,
                    error=f"HTTP {resp.status_code}",
                )

            # Validate response structure
            try:
                data = resp.json()
            except Exception:
                return CheckResult(
                    project_id=project["id"],
                    project_name=project["name"],
                    check_type="smoke",
                    success=False,
                    latency_ms=latency,
                    status_code=200,
                    error="Response is not valid JSON",
                )

            if validate_field and validate_field not in data:
                return CheckResult(
                    project_id=project["id"],
                    project_name=project["name"],
                    check_type="smoke",
                    success=False,
                    latency_ms=latency,
                    status_code=200,
                    error=f"Field '{validate_field}' missing from response. Got: {list(data.keys())[:5]}",
                )

            if attempt > 0:
                logger.info(f"Smoke OK after {attempt} retries: {project['name']}")
            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="smoke",
                success=True,
                latency_ms=latency,
                status_code=200,
                details=f"Validated OK ({latency}ms)",
            )

        except httpx.TimeoutException:
            latency = int((time.monotonic() - start) * 1000)
            if attempt < MAX_RETRIES and _should_retry(is_timeout=True):
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Smoke {project['name']}: timeout, retry in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                continue

            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="smoke",
                success=False,
                latency_ms=latency,
                error=f"Timeout ({SMOKE_TIMEOUT}s) after {MAX_RETRIES} retries",
            )

        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="smoke",
                success=False,
                latency_ms=latency,
                error=str(e),
            )


async def check_project(project: dict) -> list[CheckResult]:
    """Run all checks (health + smoke if configured) for a single project."""
    results = []
    async with httpx.AsyncClient() as client:
        health = await run_health_check(client, project)
        results.append(health)

        smoke = await run_smoke_test(client, project)
        if smoke:
            results.append(smoke)

    return results


async def check_all_projects(projects: list[dict]) -> list[CheckResult]:
    """
    Run all checks for all projects sequentially with pauses.
    Each check has built-in retry with backoff for 429/timeout/5xx.
    Sequential + pauses avoids triggering Render's rate limiter.
    """
    results = []
    async with httpx.AsyncClient() as client:
        for i, project in enumerate(projects):
            logger.info(f"Checking {project['name']} ({i + 1}/{len(projects)})")

            health = await run_health_check(client, project)
            results.append(health)

            smoke = await run_smoke_test(client, project)
            if smoke:
                results.append(smoke)

            # Pause between projects to avoid rate limiting
            if i < len(projects) - 1:
                await asyncio.sleep(PAUSE_BETWEEN_PROJECTS)

    return results
