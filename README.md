# Nirantar (निरन्तर) ⚡

> **Autonomous, continuous, industry-grade job application engine with Comet-style visual takeover, multi-resume intelligence, and zero-hallucination verification.**

[![Nirantar CI](https://github.com/Sachindrapandeyyy/nirantar/actions/workflows/ci.yml/badge.svg)](https://github.com/Sachindrapandeyyy/nirantar/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 🌟 Overview

**Nirantar** is an autonomous agent designed to relieve engineers and developers of the repetitive burden of applying to hundreds of technical jobs across multiple portals. 

Unlike blind auto-clickers or generic scrapers, **Nirantar** operates with:
- **Comet-Style Visual Takeover:** Real-time animated blue glow viewport (`#0080ff`) and floating status HUD so you can watch the agent analyze, type, upload documents, and submit forms.
- **Master Knowledge Vault:** Strict zero-hallucination data vault. All dates, education, projects, contact details, and certifications are extracted exclusively from verified candidate records.
- **Smart Tech-Stack Resume Selector:** Matches job descriptions against your specialized resumes (e.g. **Java/Spring Boot** vs. **Python/AI Systems**) and attaches the highest-scoring CV.
- **"Apply Anyway" Opportunity Policy:** Never drops or filters out a job based on posted or fixed company CTC (maximizing interview and test call rates). Volunteers salary figures only when explicitly asked.
- **Zero Cost ($0 / ₹0):** Runs entirely locally on your machine with free-tier cloud models (Gemini Flash) and offline local fallback (Ollama Qwen 2.5 on GPU).

---

## 🏗 System Architecture

```
                          [ INGESTION LAYER ]
             Telegram Groups ──► Webhook / CLI ◄── Web Scrapers
                                     │
                                     ▼
                    [ EVENT QUEUE & STATE MACHINE ]
                        (SQLite Persistent Engine)
                                     │
                                     ▼
                     [ BRAIN / DECISION CORE ]
       ┌─────────────────────────────┴─────────────────────────────┐
       ▼                                                           ▼
[ Master Vault ]                                          [ Dual-Brain LLM ]
• profile.json                                            • Gemini Flash (Free Tier)
• Java / Python Resumes                                   • Local Qwen 2.5 (Ollama)
• PAN / Aadhaar / Marksheets
                                     │
                                     ▼
                  [ COMET-STYLE VISUAL EXECUTION ]
                    • Playwright Headed Driver
                    • Pulsing Blue Glow Border HUD
                    • Human-like Jitter & Anti-Detection
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
  [ Greenhouse ]                 [ Lever ]                   [ LinkedIn / Naukri ]
                                     │
                                     ▼
                    [ FEEDBACK & AUDIT LAYER ]
            • IMAP Email Watcher (Interview / Rejection alerts)
            • Screenshot Proof Capture (proofs/*.png)
            • SQLite Audit History
```

---

## 🚀 Quickstart

### 1. Clone & Setup
```bash
git clone https://github.com/Sachindrapandeyyy/nirantar.git
cd nirantar

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .[dev]
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey):
```env
GEMINI_API_KEY=your_key_here
VAULT_DIR=C:/path/to/your/documents
```

---

## 💻 CLI Commands

### 1. Test the Visual Comet HUD
Launch a 30-second live browser demo with the pulsing blue glow and floating HUD:
```bash
python main.py test-hud
```

### 2. Apply to Any Career Portal URL
```bash
# Greenhouse example
python main.py apply "https://boards.greenhouse.io/company/jobs/12345" "Java Backend Engineer" "Company"

# Lever example
python main.py apply "https://jobs.lever.co/company/abcdef" "Python AI Engineer" "Company"
```

### 3. Check Application Status Dashboard
```bash
python main.py status
```

### 4. Monitor Email for Interview Calls
```bash
python main.py check-email
```

---

## 🛡 Privacy & Security

- All personal documents (`*.pdf`, `*.jpeg`, `*.jpg`, `PAN`, `Aadhaar`, `profile.json`) are strictly ignored by `.gitignore` and **NEVER** committed to Git.
- Free GitHub Actions CI runs mock unit tests on synthetic data without leaking personal candidate information.

---

## 📄 License

Distributed under the **MIT License**. Created by [Sachindra Shekhar Pandey](https://github.com/Sachindrapandeyyy).
