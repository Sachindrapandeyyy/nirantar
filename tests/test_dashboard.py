import pytest
import httpx
from dashboard.server import app


@pytest.mark.asyncio
async def test_dashboard_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. HTML Dashboard
        r_home = await client.get("/")
        assert r_home.status_code == 200
        assert "NIRANTAR" in r_home.text

        # 2. Stats API
        r_stats = await client.get("/api/stats")
        assert r_stats.status_code == 200
        stats = r_stats.json()
        assert stats["total_applications"] >= 75
        assert stats["candidate_name"] == "Sachindra Shekhar Pandey"
        assert "scheduler" in stats

        # 3. Jobs API
        r_jobs = await client.get("/api/jobs?limit=5")
        assert r_jobs.status_code == 200
        jobs = r_jobs.json()
        assert len(jobs) > 0

        # 4. Candidate Profile API
        r_cand = await client.get("/api/candidate")
        assert r_cand.status_code == 200
        cand = r_cand.json()
        assert cand["identity"]["name"] == "Sachindra Shekhar Pandey"
        assert "8.2" in cand["academics"]["cgpa"]
