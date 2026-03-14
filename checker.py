"""
Check engine — runs health checks and smoke tests against monitored projects.
"""

import time
from dataclasses import dataclass

import httpx


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
            resp = await client.post(url, data=payload or {}, timeout=90)
        elif payload:
            resp = await client.post(url, json=payload, timeout=90)
        else:
            resp = await client.post(url, timeout=90)

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
            error="Timeout (90s)",
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
    """Run all checks for all projects."""
    results = []
    async with httpx.AsyncClient() as client:
        for project in projects:
            health = await run_health_check(client, project)
            results.append(health)

            smoke = await run_smoke_test(client, project)
            if smoke:
                results.append(smoke)

    return results
