import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tracker.database import db, JobRecord, SessionLocal
from core.vault import vault
from core.scheduler import scheduler
from core.career_knowledge_base import get_career_knowledge_base

app = FastAPI(
    title="Nirantar Mission Control",
    description="Autonomous Multi-Agent Job Application Command Center",
    version="2.0.0"
)

# Ensure proof directories exist
PROOFS_DIR = PROJECT_ROOT / "proofs"
PROOFS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/api/stats")
async def get_stats():
    """Returns live aggregated application statistics."""
    session = SessionLocal()
    try:
        all_jobs = session.query(JobRecord).all()
        total = len(all_jobs)
        applied = sum(1 for j in all_jobs if j.status == "APPLIED")
        python_count = sum(1 for j in all_jobs if str(j.resume_type).lower() == "python")
        java_count = sum(1 for j in all_jobs if str(j.resume_type).lower() == "java")

        # Today's applications (IST)
        ist_now = scheduler.get_ist_now()
        today_start = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = 0
        for j in all_jobs:
            if j.applied_at:
                j_ist = j.applied_at.replace(tzinfo=timezone.utc).astimezone(scheduler.get_ist_now().tzinfo)
                if j_ist >= today_start:
                    today_count += 1

        # Portals breakdown
        portals = {}
        for j in all_jobs:
            p = j.portal or "Other"
            portals[p] = portals.get(p, 0) + 1

        profile = vault.get_profile()

        return {
            "total_applications": total,
            "verified_applied": applied,
            "today_applied": today_count,
            "python_stack_count": python_count,
            "java_stack_count": java_count,
            "portals": portals,
            "scheduler": scheduler.get_status_summary(),
            "candidate_name": profile.full_name,
            "profile_score": "95%",
            "resdex_rank": "#1 Active (2-Hr Dot Sync)",
            "target_roles": "Dual-Stack Software Engineer (Python & Java 0-2 Yrs Freshers)"
        }
    finally:
        session.close()


@app.get("/api/jobs")
async def get_jobs(limit: int = 50, stack: Optional[str] = None, portal: Optional[str] = None):
    """Returns list of tracked job applications."""
    session = SessionLocal()
    try:
        q = session.query(JobRecord)
        if stack and stack.lower() != "all":
            q = q.filter(JobRecord.resume_type == stack.lower())
        if portal and portal.lower() != "all":
            q = q.filter(JobRecord.portal.like(f"%{portal}%"))

        jobs = q.order_by(JobRecord.id.desc()).limit(limit).all()
        results = []
        for j in jobs:
            has_proof = False
            proof_filename = ""
            if j.screenshot_path and Path(j.screenshot_path).exists():
                has_proof = True
                proof_filename = Path(j.screenshot_path).name

            results.append({
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "portal": j.portal,
                "url": j.url,
                "match_score": j.match_score,
                "resume_type": j.resume_type,
                "status": j.status,
                "has_proof": has_proof,
                "proof_filename": proof_filename,
                "applied_at": j.applied_at.strftime("%d %b %Y, %I:%M %p") if j.applied_at else "Queued"
            })
        return results
    finally:
        session.close()


@app.get("/api/proof/{filename}")
async def get_proof_image(filename: str):
    """Serves application screenshot proof from disk."""
    # Search in proofs root and subdirectories
    for root, _, files in os.walk(str(PROOFS_DIR)):
        if filename in files:
            file_path = Path(root) / filename
            return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Proof screenshot not found")


@app.post("/api/control/trigger_email_check")
async def trigger_email_check():
    """Triggers real-time Gmail interview invite inspection."""
    from listeners.email_watcher import EmailWatcher
    from core.notifier import notify_user
    ew = EmailWatcher()
    alerts = ew.check_inbox()
    for alert in alerts:
        if alert.get("type") == "INTERVIEW":
            notify_user(
                title="🎯 Interview Invitation Detected!",
                message=f"From: {alert.get('from')[:30]} | {alert.get('subject')[:40]}",
                alert_type="interview"
            )
    return {"status": "success", "alerts_found": len(alerts), "alerts": alerts}


@app.get("/api/candidate")
async def get_candidate():
    """Returns candidate credentials and knowledge base."""
    kb = get_career_knowledge_base("python")
    return {
        "identity": {
            "name": kb["full_name"],
            "email": kb["email"],
            "phone": kb["full_phone"],
            "location": f"{kb['city']}, {kb['country']}",
            "linkedin": kb["linkedin"],
            "github": kb["github"],
            "portfolio": kb["portfolio"]
        },
        "academics": {
            "university": kb["university"],
            "degree": kb["degree"],
            "branch": kb["branch"],
            "batch": f"{kb['college_start_year']}-{kb['grad_year']}",
            "cgpa": kb["cgpa"],
            "12th": kb["12th_percentage"] + "%",
            "10th": kb["10th_percentage"] + "%"
        },
        "experience": {
            "recent_employer": kb["current_company"],
            "role": kb["current_role"],
            "experience_years": kb["experience_years"] + " yrs (3 months)"
        },
        "compensation": {
            "current_ctc": kb["current_ctc_lpa"],
            "expected_ctc": kb["expected_ctc_lpa"],
            "notice_period": kb["notice_period"]
        }
    }


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the Mission Control HTML."""
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Nirantar Dashboard Template Missing</h1>")


def run_dashboard_server(port: int = 8000, open_browser: bool = True):
    """Launches Uvicorn server and optionally opens browser."""
    import uvicorn
    import webbrowser

    if open_browser:
        def _open():
            import time
            time.sleep(1.2)
            webbrowser.open(f"http://localhost:{port}")
        import threading
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    run_dashboard_server()
