from __future__ import annotations

import threading
import time
from uuid import uuid4

import pytest

from app.main import (
    app,
    configure_inference_provider,
    configure_object_storage,
    configure_persistent_store,
    make_id,
    store,
)
from fastapi.testclient import TestClient

client = TestClient(app)


def auth_headers():
    payload = {
        "email": f"worker-{uuid4().hex}@gameuiagent.dev",
        "password": "secret-pass",
        "name": "Worker Test User",
    }
    created = client.post("/api/auth/register", json=payload)
    assert created.status_code == 201
    logged_in = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_store(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "worker-test.sqlite3"))
    configure_object_storage(str(tmp_path / "objects"))
    configure_inference_provider("local-deterministic")
    monkeypatch.setenv("GAMEUIAGENT_WORKER_EMBEDDED", "1")
    monkeypatch.setenv("GAMEUIAGENT_WORKER_POLL_INTERVAL", "0.01")
    yield
    configure_inference_provider("local-deterministic")


def test_embedded_worker_dequeues_and_completes_job(tmp_path, monkeypatch):
    import worker as worker_module

    monkeypatch.setattr(worker_module, "WORKER_ID", "test-worker-1")
    monkeypatch.setattr(worker_module, "USE_EMBEDDED", True)
    monkeypatch.setattr(worker_module, "WORKER_POLL_INTERVAL", 0.01)

    headers = auth_headers()

    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Worker Test Project",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 512},
        },
    ).json()

    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "cyberpunk game UI",
            "execution_mode": "queued",
        },
    ).json()

    assert job["status"] == "queued"

    worker_module._shutdown = False

    dequeued = worker_module.dequeue_next_job()
    assert dequeued is not None
    assert dequeued["queue_item"]["status"] == "locked"
    assert dequeued["queue_item"]["worker"] == "test-worker-1"
    assert dequeued["job"]["status"] == "running"

    success, result = worker_module.execute_job(dequeued)
    assert success is True
    assert result is not None

    updated_job = store["jobs"].get(job["id"])
    assert updated_job["status"] == "succeeded"
    assert updated_job["progress"] == 100
    assert updated_job["result_asset"] is not None


def test_embedded_worker_handles_failed_inference(tmp_path, monkeypatch):
    import worker as worker_module

    monkeypatch.setattr(worker_module, "WORKER_ID", "test-worker-fail")
    monkeypatch.setattr(worker_module, "USE_EMBEDDED", True)

    configure_inference_provider("failing")

    headers = auth_headers()

    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Worker Fail Project",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 512},
        },
    ).json()

    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "will fail",
            "execution_mode": "queued",
        },
    ).json()

    dequeued = worker_module.dequeue_next_job()
    assert dequeued is not None

    success, error = worker_module.execute_job(dequeued)
    assert success is False
    assert "failed" in str(error).lower() or "Inference provider" in str(error)

    updated_job = store["jobs"].get(job["id"])
    assert updated_job["status"] == "failed"
    assert updated_job["error"] is not None

    configure_inference_provider("local-deterministic")


def test_worker_signal_shutdown(tmp_path, monkeypatch):
    import worker as worker_module

    monkeypatch.setattr(worker_module, "WORKER_ID", "test-shutdown-worker")
    monkeypatch.setattr(worker_module, "USE_EMBEDDED", True)

    worker_module._shutdown = False
    worker_module.handle_signal(15, None)
    assert worker_module._shutdown is True


def test_worker_idle_when_no_jobs(tmp_path, monkeypatch):
    import worker as worker_module

    monkeypatch.setattr(worker_module, "WORKER_ID", "test-idle-worker")
    monkeypatch.setattr(worker_module, "USE_EMBEDDED", True)

    result = worker_module.dequeue_next_job()
    assert result is None
