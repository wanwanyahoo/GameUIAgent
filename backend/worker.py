from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timezone
from os import getenv

import httpx

from app.main import (
    complete_ai_job,
    configure_inference_provider,
    configure_object_storage,
    configure_persistent_store,
    configure_worker_token,
    inference_provider_name,
    object_storage,
    run_inference_provider,
    store,
)

WORKER_ID = getenv("GAMEUIAGENT_WORKER_ID", f"worker-{int(time.time())}")
WORKER_POLL_INTERVAL = float(getenv("GAMEUIAGENT_WORKER_POLL_INTERVAL", "2.0"))
WORKER_MAX_RETRIES = int(getenv("GAMEUIAGENT_WORKER_MAX_RETRIES", "3"))
DB_PATH = getenv("GAMEUIAGENT_DB_PATH", "data/gameuiagent.db")
OBJECT_STORAGE_ROOT = getenv("GAMEUIAGENT_OBJECT_STORAGE", "data/objects")
BASE_URL = getenv("GAMEUIAGENT_API_BASE_URL", "http://localhost:8000")
WORKER_TOKEN = getenv("GAMEUIAGENT_WORKER_TOKEN", "")
USE_EMBEDDED = getenv("GAMEUIAGENT_WORKER_EMBEDDED", "1") == "1"

_shutdown = False


def handle_signal(signum, frame):
    global _shutdown
    print(f"[worker] received signal {signum}, shutting down gracefully...", flush=True)
    _shutdown = True


def configure_embedded_worker():
    configure_persistent_store(DB_PATH)
    configure_object_storage(OBJECT_STORAGE_ROOT)
    configure_inference_provider(inference_provider_name)
    configure_worker_token(WORKER_TOKEN or None)


def dequeue_next_job():
    if USE_EMBEDDED:
        items = [item for item in store["ai_job_queue"].values() if item["status"] == "queued"]
        if not items:
            return None
        queue_item = items[0]
        job = store["jobs"].get(queue_item["job_id"])
        project = store["projects"].get(queue_item["project_id"])
        if not job or not project:
            queue_item["status"] = "failed"
            queue_item["error"] = "Queued job lost its project or job record"
            store.flush()
            return None
        queue_item["status"] = "locked"
        queue_item["worker"] = WORKER_ID
        queue_item["locked_at"] = datetime.now(timezone.utc).isoformat()
        job["status"] = "running"
        job["progress"] = 25
        store.flush()
        return {"queue_item": queue_item, "job": job, "project": project}
    else:
        headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
        response = httpx.post(f"{BASE_URL}/api/worker/jobs/dequeue", headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data["status"] != "dequeued":
            return None
        return data


def complete_job(queue_id, status, result=None, error=None):
    if USE_EMBEDDED:
        from app.main import append_audit_event

        queue_item = store["ai_job_queue"].get(queue_id)
        if not queue_item:
            return None
        job = store["jobs"].get(queue_item["job_id"])
        project = store["projects"].get(queue_item["project_id"])
        if not job or not project:
            queue_item["status"] = "failed"
            queue_item["error"] = "Job or project not found"
            store.flush()
            return None

        if status == "succeeded":
            queue_item["status"] = "succeeded"
            if result:
                complete_ai_job(project, job, result)
            else:
                job["status"] = "succeeded"
                job["progress"] = 100
                job["completed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            queue_item["status"] = "failed"
            queue_item["error"] = error or "Worker failed"
            job["status"] = "failed"
            job["progress"] = 0
            job["error"] = error or "Worker failed"

        job["queue"] = queue_item
        if job["status"] in {"succeeded", "failed"}:
            append_audit_event(
                project["id"],
                f"ai_job_{job['status']}",
                None,
                "ai_job",
                job["id"],
                status_value=job["status"],
                metadata={"queue_id": queue_item["id"], "worker": queue_item.get("worker")},
            )
        store.flush()
        return {"status": job["status"], "job": job}
    else:
        headers = {"X-Worker-Token": WORKER_TOKEN, "Content-Type": "application/json"} if WORKER_TOKEN else {}
        payload = {"status": status}
        if result:
            payload["result"] = result
        if error:
            payload["error"] = error
        response = httpx.post(
            f"{BASE_URL}/api/worker/jobs/{queue_id}/complete",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


def execute_job(dequeued):
    queue_item = dequeued["queue_item"]
    job = dequeued["job"]
    project = dequeued["project"]

    if USE_EMBEDDED:
        try:
            result = run_inference_provider(project, job)
            complete_ai_job(project, job, result)
            queue_item["status"] = "succeeded"
            job["queue"] = queue_item
            store.flush()
            return True, result
        except RuntimeError as exc:
            queue_item["status"] = "failed"
            queue_item["error"] = str(exc)
            job["status"] = "failed"
            job["error"] = str(exc)
            job["progress"] = 0
            job["queue"] = queue_item
            store.flush()
            return False, str(exc)
    else:
        try:
            result = run_inference_provider(project, job)
            complete_job(queue_item["id"], "succeeded", result=result)
            return True, result
        except RuntimeError as exc:
            complete_job(queue_item["id"], "failed", error=str(exc))
            return False, str(exc)


def worker_loop():
    print(f"[worker] {WORKER_ID} starting (provider={inference_provider_name}, embedded={USE_EMBEDDED})", flush=True)
    consecutive_idle = 0

    while not _shutdown:
        try:
            dequeued = dequeue_next_job()
            if not dequeued:
                consecutive_idle += 1
                if consecutive_idle <= 3 or consecutive_idle % 10 == 0:
                    print(f"[worker] {WORKER_ID} idle, sleeping {WORKER_POLL_INTERVAL}s", flush=True)
                time.sleep(WORKER_POLL_INTERVAL)
                continue

            consecutive_idle = 0
            queue_item = dequeued["queue_item"]
            job = dequeued["job"]
            project = dequeued["project"]
            job_id = job.get("id", queue_item.get("job_id", "unknown"))
            kind = job.get("kind", "unknown")
            project_name = project.get("name", "unknown") if isinstance(project, dict) else "unknown"

            print(f"[worker] {WORKER_ID} picked job {job_id} ({kind}) for project '{project_name}'", flush=True)

            success, result = execute_job(dequeued)
            if success:
                print(f"[worker] {WORKER_ID} completed job {job_id} successfully", flush=True)
            else:
                print(f"[worker] {WORKER_ID} job {job_id} failed: {result}", flush=True)

        except Exception as exc:
            print(f"[worker] {WORKER_ID} error in loop: {exc}", flush=True)
            time.sleep(WORKER_POLL_INTERVAL * 2)

    print(f"[worker] {WORKER_ID} stopped cleanly", flush=True)


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if USE_EMBEDDED:
        configure_embedded_worker()
    else:
        configure_object_storage(OBJECT_STORAGE_ROOT)
        configure_inference_provider(inference_provider_name)

    try:
        worker_loop()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
