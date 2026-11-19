import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from core.vault import vault
from tracker.database import db
from core.matcher import matcher
from browser.driver import BrowserDriver
from browser.overlay import CometHUD
from listeners.email_watcher import EmailWatcher
from adapters.greenhouse import GreenhouseAdapter
from adapters.lever import LeverAdapter
from adapters.linkedin import LinkedInEasyApplyAdapter
from adapters.naukri import NaukriAdapter
from brain.gemini_provider import GeminiProvider
from core.models import JobListing

app = FastAPI(title="Nirantar Job Automation Dashboard")


class ApplyRequest(BaseModel):
    url: str
    title: Optional[str] = "Software Engineer"
    company: Optional[str] = "Target Company"


# Embedded Sleek Dark Web Dashboard UI
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nirantar (निरन्तर) - AI Job Automation Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #060913; color: #f1f5f9; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .glow-box { box-shadow: 0 0 35px -5px rgba(0, 140, 255, 0.3); }
        .glow-cyan { box-shadow: 0 0 25px -5px rgba(0, 229, 255, 0.4); }
    </style>
</head>
<body class="min-h-screen p-6 md:p-10 flex flex-col items-center">
    <div class="w-full max-w-6xl space-y-8">
        
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-slate-800 gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <span class="w-3.5 h-3.5 rounded-full bg-cyan-400 animate-pulse shadow-lg shadow-cyan-500"></span>
                    <h1 class="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
                        NIRANTAR <span class="text-xs font-mono font-normal px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">v1.0 ACTIVE</span>
                    </h1>
                </div>
                <p class="text-slate-400 text-sm mt-1">Autonomous, continuous job application engine with Comet visual takeover.</p>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="checkEmail()" class="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-500 text-sm font-semibold text-slate-200 transition">
                    📬 Check Recruiter Emails
                </button>
                <button onclick="triggerHudDemo()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-sm font-bold text-white shadow-lg shadow-blue-500/30 transition">
                    🔵 Test Comet Blue Glow
                </button>
            </div>
        </header>

        <!-- Profile & Vault Quick Bar -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
                <span class="text-xs font-semibold text-slate-400 tracking-wider uppercase">Candidate</span>
                <p id="cand-name" class="text-lg font-bold text-white mt-1">Sachindra Shekhar Pandey</p>
                <p class="text-xs text-slate-400">sachindrapandey328@gmail.com</p>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
                <span class="text-xs font-semibold text-slate-400 tracking-wider uppercase">Experience & Notice</span>
                <p class="text-lg font-bold text-cyan-400 mt-1">0.3 Yrs (Fresher / NTPC)</p>
                <p class="text-xs text-slate-400">Notice: Immediate (0 Days)</p>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
                <span class="text-xs font-semibold text-slate-400 tracking-wider uppercase">CTC Strategy</span>
                <p class="text-lg font-bold text-emerald-400 mt-1">Apply Regardless of CTC</p>
                <p class="text-xs text-slate-400">If asked: Current 6L | Expected 7.5L</p>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
                <span class="text-xs font-semibold text-slate-400 tracking-wider uppercase">Active Resumes</span>
                <p class="text-sm font-semibold text-slate-200 mt-1">☕ Java Spring Boot (PDF)</p>
                <p class="text-sm font-semibold text-slate-200">🐍 Python AI Backend (PDF)</p>
            </div>
        </div>

        <!-- Quick Apply Action Card -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 glow-box">
            <h2 class="text-xl font-bold text-white mb-2">🚀 Launch Autonomous Application</h2>
            <p class="text-sm text-slate-400 mb-6">Paste any job URL from Greenhouse, Lever, Workday, LinkedIn or Naukri. Nirantar will match the resume, launch the Comet browser, fill verified data, and submit proof.</p>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Job Application URL *</label>
                    <input id="job-url" type="url" placeholder="https://boards.greenhouse.io/... or https://jobs.lever.co/..." class="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 focus:border-cyan-400 focus:outline-none text-white text-sm font-mono transition">
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Job Title</label>
                        <input id="job-title" type="text" placeholder="e.g. Java Backend Engineer" class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 focus:border-cyan-400 focus:outline-none text-white text-sm transition">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Company Name</label>
                        <input id="job-company" type="text" placeholder="e.g. Canonical / Google" class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 focus:border-cyan-400 focus:outline-none text-white text-sm transition">
                    </div>
                </div>
                <div class="pt-2 flex items-center gap-4">
                    <button id="apply-btn" onclick="submitApplication()" class="px-8 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm tracking-wide transition shadow-lg shadow-cyan-500/30 flex items-center gap-2">
                        <span>⚡ Launch Agent Apply</span>
                    </button>
                    <span id="apply-status" class="text-sm font-mono text-slate-400">Ready</span>
                </div>
            </div>
        </div>

        <!-- Live History & Tracker Table -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 md:p-8">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h3 class="text-lg font-bold text-white">📋 Applied Jobs & Status Log</h3>
                    <p class="text-xs text-slate-400">All applications persisted in local SQLite database</p>
                </div>
                <button onclick="loadJobs()" class="text-xs text-cyan-400 hover:underline">Refresh Table</button>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="text-xs uppercase bg-slate-950 text-slate-400 font-mono">
                        <tr>
                            <th class="p-3.5">ID</th>
                            <th class="p-3.5">Company</th>
                            <th class="p-3.5">Title</th>
                            <th class="p-3.5">Portal</th>
                            <th class="p-3.5">Resume</th>
                            <th class="p-3.5">Score</th>
                            <th class="p-3.5">Status</th>
                        </tr>
                    </thead>
                    <tbody id="jobs-body" class="divide-y divide-slate-800 font-normal">
                        <!-- Loaded dynamically -->
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        async function loadJobs() {
            try {
                const res = await fetch('/api/jobs');
                const jobs = await res.json();
                const tbody = document.getElementById('jobs-body');
                tbody.innerHTML = '';
                if (jobs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="p-4 text-center text-slate-500">No applications yet. Paste a link above to start!</td></tr>';
                    return;
                }
                jobs.forEach(j => {
                    const row = document.createElement('tr');
                    const badgeClass = j.status === 'APPLIED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30';
                    row.innerHTML = `
                        <td class="p-3.5 font-mono text-xs text-slate-500">${j.id}</td>
                        <td class="p-3.5 font-semibold text-white">${j.company}</td>
                        <td class="p-3.5">${j.title}</td>
                        <td class="p-3.5 text-xs font-mono text-blue-400">${j.portal}</td>
                        <td class="p-3.5 font-mono text-xs text-amber-400">${j.resume_type.toUpperCase()}</td>
                        <td class="p-3.5 font-mono text-xs">${j.match_score.toFixed(2)}</td>
                        <td class="p-3.5"><span class="px-2.5 py-1 rounded-full text-xs font-bold ${badgeClass}">${j.status}</span></td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (err) {
                console.error(err);
            }
        }

        async function submitApplication() {
            const url = document.getElementById('job-url').value.trim();
            const title = document.getElementById('job-title').value.trim() || 'Software Engineer';
            const company = document.getElementById('job-company').value.trim() || 'Company';
            const statusEl = document.getElementById('apply-status');
            const btn = document.getElementById('apply-btn');

            if (!url) {
                alert('Please enter a job URL!');
                return;
            }

            btn.disabled = true;
            statusEl.innerText = '🚀 Agent running live... Check your screen!';
            statusEl.className = 'text-sm font-mono text-cyan-400 animate-pulse';

            try {
                const res = await fetch('/api/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, title, company })
                });
                const data = await res.json();
                statusEl.innerText = data.message || 'Completed!';
                statusEl.className = 'text-sm font-mono text-emerald-400';
                loadJobs();
            } catch (err) {
                statusEl.innerText = 'Error launching application.';
                statusEl.className = 'text-sm font-mono text-rose-400';
            } finally {
                btn.disabled = false;
            }
        }

        async function triggerHudDemo() {
            const res = await fetch('/api/test-hud');
            alert('Comet Blue Glow live test initiated on your screen!');
        }

        async function checkEmail() {
            const res = await fetch('/api/check-email');
            const data = await res.json();
            alert('Email inbox check completed! Found: ' + data.count + ' recruiter updates.');
        }

        loadJobs();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_DASHBOARD


@app.get("/api/jobs")
async def list_jobs():
    records = db.list_recent_jobs(limit=30)
    return [
        {
            "id": r.id,
            "company": r.company,
            "title": r.title,
            "portal": r.portal,
            "url": r.url,
            "resume_type": r.resume_type,
            "match_score": r.match_score,
            "status": r.status,
            "screenshot_path": r.screenshot_path,
        }
        for r in records
    ]


@app.post("/api/apply")
async def apply_job(req: ApplyRequest, background_tasks: BackgroundTasks):
    match_res = matcher.match(title=req.title, description="")
    
    # Run application in background
    async def do_apply():
        adapters = [
            GreenhouseAdapter(),
            LeverAdapter(),
            LinkedInEasyApplyAdapter(),
            NaukriAdapter()
        ]
        target_adapter = None
        for a in adapters:
            if a.can_handle(req.url):
                target_adapter = a
                break
        
        if not target_adapter:
            return
        
        job = JobListing(
            title=req.title,
            company=req.company,
            url=req.url,
            match_result=match_res
        )
        
        driver = BrowserDriver()
        try:
            page = await driver.start()
            res = await target_adapter.apply(job, page, GeminiProvider())
            db.save_job(
                title=job.title,
                company=job.company,
                portal=target_adapter.__class__.__name__,
                url=job.url,
                match_score=match_res.score,
                resume_type=match_res.resume_type
            )
            db.update_job_status(job.url, "APPLIED" if res.success else "FAILED", res.screenshot_path)
            await asyncio.sleep(4)
        finally:
            await driver.close()

    background_tasks.add_task(do_apply)
    return {
        "status": "QUEUED",
        "message": f"Nirantar launched for {req.company} using {match_res.resume_type.upper()} Resume!"
    }


@app.get("/api/test-hud")
async def test_hud(background_tasks: BackgroundTasks):
    async def run_hud():
        driver = BrowserDriver()
        try:
            page = await driver.start()
            await page.goto("https://httpbin.org/forms/post")
            await CometHUD.inject(page)
            await CometHUD.update_status(page, "Comet Takeover Demo: Active on your screen!")
            await asyncio.sleep(6)
        finally:
            await driver.close()
    
    background_tasks.add_task(run_hud)
    return {"status": "ok"}


@app.get("/api/check-email")
async def check_email_endpoint():
    watcher = EmailWatcher()
    results = watcher.check_inbox()
    return {"status": "ok", "count": len(results), "results": results}


def start_server():
    uvicorn.run("ui.dashboard:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start_server()
