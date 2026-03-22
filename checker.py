"""
Check engine — runs health checks and smoke tests against monitored projects.

Includes a wake-up phase for Render free tier services that sleep after 15 min
of inactivity. Without wake-up, cold starts (30-60s) cause false timeout alerts.
"""

import asyncio
import time
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("shipwatcher.checker")


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


async def run_health_check(client: httpx.AsyncClient, project: dict) -> CheckResult:
    url = project["url"] + project["health_endpoint"]
    method = project.get("health_method", "GET")
    start = time.monotonic()

    try:
        if method.upper() == "POST":
            resp = await client.post(url, timeout=30)
        else:
            resp = await client.get(url, timeout=30)

        latency = int((time.monotonic() - start) * 1000)

        if resp.status_code == 200:
            return CheckResult(
                project_id=project["id"],
                project_name=project["name"],
                check_type="health",
                success=True,
                latency_ms=latency,
                status_code=resp.status_code,
            )
        else:
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
        return CheckResult(
            project_id=project["id"],
            project_name=project["name"],
            check_type="health",
            success=False,
            latency_ms=latency,
            error="Timeout (30s)",
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
    start = time.monotonic()

    try:
        if payload_type == "form":
            resp = await client.post(url, data=payload or {}, timeout=180)
        elif payload:
            resp = await client.post(url, json=payload, timeout=180)
        else:
            resp = await client.post(url, timeout=180)

        latency = int((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
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
        return CheckResult(
            project_id=project["id"],
            project_name=project["name"],
            check_type="smoke",
            success=False,
            latency_ms=latency,
            error="Timeout (180s)",
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
    """Run all checks (health + smoke if configured) for a single project.
    Includes wake-up for individual project checks too."""
    async with httpx.AsyncClient() as client:
        # Wake up the service first (handles cold start)
        await _wake_service(client, project)

    # Now run checks with a fresh client
    results = []
    async with httpx.AsyncClient() as client:
        health = await run_health_check(client, project)
        results.append(health)

        smoke = await run_smoke_test(client, project)
        if smoke:
            results.append(smoke)

    return results


async def _wake_service(client: httpx.AsyncClient, project: dict) -> bool:
    """
    Send a wake-up request to a sleeping Render free tier service.
    Uses a 90s timeout — we don't care about the response, just that the
    service process starts. Returns True if the service responded.
    """
    url = project["url"] + project["health_endpoint"]
    try:
        resp = await client.get(url, timeout=90)
        logger.info(f"Wake-up OK: {project['name']} ({resp.status_code})")
        return True
    except Exception as e:
        logger.warning(f"Wake-up failed: {project['name']} — {e}")
        return False


async def _wake_all_services(projects: list[dict]):
    """
    Wake all services in parallel before running real checks.
    This prevents false timeout alerts from Render cold starts.
    """
    logger.info(f"Waking up {len(projects)} services...")
    async with httpx.AsyncClient() as client:
        tasks = [_wake_service(client, p) for p in projects]
        results = await asyncio.gather(*tasks)

    awake = sum(1 for r in results if r)
    logger.info(f"Wake-up done: {awake}/{len(projects)} responded")

    # Small buffer for services that just woke up
    if awake < len(projects):
        logger.info("Some services slow to wake — waiting 5s before checks")
        await asyncio.sleep(5)


async def check_all_projects(projects: list[dict]) -> list[CheckResult]:
    """
    Run all checks for all projects.
    Phase 1: Wake all services in parallel (handles Render cold starts).
    Phase 2: Run actual health checks + smoke tests.
    """
    # Phase 1 — Wake up sleeping services
    await _wake_all_services(projects)

    # Phase 2 — Real checks (services should be warm now)
    results = []
    async with httpx.AsyncClient() as client:
        for project in projects:
            health = await run_health_check(client, project)
            results.append(health)

            smoke = await run_smoke_test(client, project)
            if smoke:
                results.append(smoke)

    return results
