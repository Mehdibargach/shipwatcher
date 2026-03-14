"""
ShipWatcher API — Backend FastAPI
"""

import re
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import store
import checker

app = FastAPI(title="ShipWatcher", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.(lovableproject\.com|lovable\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    url: str
    health_endpoint: str = "/health"
    health_method: str = "GET"
    smoke_endpoint: str | None = None
    smoke_method: str = "POST"
    smoke_payload: dict | None = None
    smoke_payload_type: str = "json"  # "json" or "form"
    smoke_validate_field: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    health_endpoint: str | None = None
    health_method: str | None = None
    smoke_endpoint: str | None = None
    smoke_method: str | None = None
    smoke_payload: dict | None = None
    smoke_payload_type: str | None = None
    smoke_validate_field: str | None = None


# ── URL validation ────────────────────────────────────────────────────────────

URL_PATTERN = re.compile(r"^https?://[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}")


def validate_url(url: str):
    if not URL_PATTERN.match(url):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URL: '{url}'. Must start with http:// or https:// and be a valid domain.",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "shipwatcher", "version": "0.1.0"}


@app.get("/projects")
def list_projects():
    return store.list_projects()


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/projects", status_code=201)
def create_project(body: ProjectCreate):
    validate_url(body.url)
    project = store.add_project(
        name=body.name,
        url=body.url,
        health_endpoint=body.health_endpoint,
        health_method=body.health_method,
        smoke_endpoint=body.smoke_endpoint,
        smoke_method=body.smoke_method,
        smoke_payload=body.smoke_payload,
        smoke_payload_type=body.smoke_payload_type,
        smoke_validate_field=body.smoke_validate_field,
    )
    return project


@app.put("/projects/{project_id}")
def update_project(project_id: str, body: ProjectUpdate):
    updates = body.model_dump(exclude_none=True)
    if "url" in updates:
        validate_url(updates["url"])
    project = store.update_project(project_id, updates)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    deleted = store.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@app.post("/projects/{project_id}/check")
async def check_single_project(project_id: str):
    """Run health check (+ smoke test if configured) on a single project."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = await checker.check_project(project)

    # Update last_check timestamp
    store.update_project(project_id, {
        "last_check": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "project_id": project_id,
        "project_name": project["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": [
            {
                "check_type": r.check_type,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "status_code": r.status_code,
                "error": r.error or None,
                "details": r.details or None,
            }
            for r in results
        ],
    }


@app.post("/check-all")
async def check_all():
    """Run all checks on all projects. Pre-demo mode."""
    projects = store.list_projects()
    if not projects:
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "results": [], "summary": {"total": 0}}

    all_results = await checker.check_all_projects(projects)

    # Update last_check for all projects
    now = datetime.now(timezone.utc).isoformat()
    for p in projects:
        store.update_project(p["id"], {"last_check": now})

    passed = sum(1 for r in all_results if r.success)
    failed = sum(1 for r in all_results if not r.success)

    return {
        "timestamp": now,
        "results": [
            {
                "project_id": r.project_id,
                "project_name": r.project_name,
                "check_type": r.check_type,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "status_code": r.status_code,
                "error": r.error or None,
                "details": r.details or None,
            }
            for r in all_results
        ],
        "summary": {
            "total": len(all_results),
            "passed": passed,
            "failed": failed,
            "all_pass": failed == 0,
        },
    }
