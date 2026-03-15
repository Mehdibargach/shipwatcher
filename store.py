"""
Project store — JSON file-based storage for monitored projects.
Seed data is loaded from seed.json on first boot (survives redeploys).
Runtime data is stored in data/projects.json (ephemeral on Render).
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

STORE_PATH = Path("data/projects.json")
SEED_PATH = Path("seed.json")


def _load() -> list[dict]:
    if STORE_PATH.exists():
        with open(STORE_PATH, "r") as f:
            data = json.load(f)
            if data:
                return data

    # First boot or after redeploy: load seed data
    if SEED_PATH.exists():
        with open(SEED_PATH, "r") as f:
            seed = json.load(f)
        # Save seed to runtime store
        _save(seed)
        return seed

    return []


def _save(projects: list[dict]):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(projects, f, indent=2)


def list_projects() -> list[dict]:
    return _load()


def get_project(project_id: str) -> dict | None:
    projects = _load()
    for p in projects:
        if p["id"] == project_id:
            return p
    return None


def add_project(
    name: str,
    url: str,
    health_endpoint: str = "/health",
    health_method: str = "GET",
    smoke_endpoint: str | None = None,
    smoke_method: str = "POST",
    smoke_payload: dict | None = None,
    smoke_payload_type: str = "json",
    smoke_validate_field: str | None = None,
) -> dict:
    projects = _load()
    project = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "url": url.rstrip("/"),
        "health_endpoint": health_endpoint,
        "health_method": health_method,
        "smoke_endpoint": smoke_endpoint,
        "smoke_method": smoke_method,
        "smoke_payload": smoke_payload,
        "smoke_payload_type": smoke_payload_type,
        "smoke_validate_field": smoke_validate_field,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_check": None,
    }
    projects.append(project)
    _save(projects)
    return project


def update_project(project_id: str, updates: dict) -> dict | None:
    projects = _load()
    for i, p in enumerate(projects):
        if p["id"] == project_id:
            projects[i].update(updates)
            _save(projects)
            return projects[i]
    return None


def delete_project(project_id: str) -> bool:
    projects = _load()
    new_projects = [p for p in projects if p["id"] != project_id]
    if len(new_projects) == len(projects):
        return False
    _save(new_projects)
    return True
