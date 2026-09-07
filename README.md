<![CDATA[# 🔍 TruthLens — AI-Powered Rumour Verification Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![DuckDuckGo](https://img.shields.io/badge/DuckDuckGo-Search-DE5833?style=for-the-badge&logo=duckduckgo&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A modular, multi-agent rumour verification system that leverages Google's Gemini 2.5 Flash AI model to fact-check claims against trusted web sources in real time.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [AI Model Details](#-ai-model-details)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [How to Run](#-how-to-run)
- [Usage Examples](#-usage-examples)
- [How It Works](#-how-it-works)
- [Design Principles](#-design-principles)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🌟 Overview

TruthLens is a terminal-based AI agent that verifies rumours and claims by:

1. **Cleaning** raw user input into a normalized claim
2. **Checking** a local cache for previously verified claims
3. **Searching** the web for fact-check evidence via DuckDuckGo
4. **Analyzing** the evidence using Google Gemini 2.5 Flash AI
5. **Producing** a structured verdict with confidence score and explanation
6. **Caching** results locally to avoid redundant API calls

---

## 🤖 AI Model Details

| Property | Details |
|---|---|
| **Model Name** | `gemini-2.5-flash` |
| **Provider** | Google (via Generative Language API) |
| **API Endpoint** | `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent` |
| **Temperature** | `0.3` (low — for factual, deterministic responses) |
| **Max Output Tokens** | `2048` |
| **Response Format** | Structured JSON (`application/json`) |
| **Purpose in TruthLens** | Analyzes fact-check evidence and generates a verdict (`True`, `False`, `Partially True`, or `Unverified`) with a confidence score (0–100) and detailed explanation |

### Why Gemini 2.5 Flash?

- ⚡ **Speed** — Flash variant optimized for low-latency responses
- 🎯 **Accuracy** — Strong reasoning capabilities for evidence analysis
- 💰 **Cost-Effective** — Significantly cheaper than larger model variants
- 📊 **Structured Output** — Native support for JSON response formatting

---

## 🏗 Architecture

TruthLens uses a **sequential multi-agent pipeline** where each agent has a single responsibility:

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                             │
│                 "COVID vaccines contain 5G chips"            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │      ClaimAgent        │  ← Normalizes & cleans input
              │  (Input Processing)    │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     MemoryAgent        │  ← Checks local JSON cache
              │    (Cache Lookup)      │     for previous results
              └────────────┬───────────┘
                           │
                    ┌──────┴──────┐
                    │             │
               [CACHED]     [NOT FOUND]
                    │             │
                    ▼             ▼
              Return         ┌────────────────────────┐
              Result         │    EvidenceAgent        │  ← Searches DuckDuckGo
                             │  (Evidence Retrieval)   │     for fact-check articles
                             └────────────┬───────────┘
                                          │
                                          ▼
                             ┌────────────────────────┐
                             │   ReasoningAgent       │  ← Sends evidence to
                             │  (Verdict Generation)  │     Gemini 2.5 Flash
                             └────────────┬───────────┘
                                          │
                                          ▼
                             ┌────────────────────────┐
                             │     MemoryAgent        │  ← Saves result to
                             │    (Cache Save)        │     history.json
                             └────────────┬───────────┘
                                          │
                                          ▼
                             ┌────────────────────────┐
                             │  VERIFICATION REPORT   │
                             │  Verdict · Confidence  │
                             │  Explanation · Sources  │
                             └────────────────────────┘
```

---

## 📁 Project Structure

```
RumourAgent/
├── main.py                      # 🚀 Entry point — orchestration & terminal UI
├── requirements.txt             # 📦 Python dependencies
├── .env                         # 🔑 API keys (you create this)
├── .gitignore                   # Git ignore rules
├── README.md                    # 📖 This file
│
├── agents/                      # 🤖 Agent modules (business logic)
│   ├── __init__.py
│   ├── claim_agent.py           #   → Input normalization & cleaning
│   ├── evidence_agent.py        #   → Evidence retrieval delegation
│   ├── memory_agent.py          #   → JSON-based verification caching
│   └── reasoning_agent.py       #   → AI-powered verdict generation
│
├── services/                    # ⚙️ External service wrappers
│   ├── __init__.py
│   ├── factcheck_service.py     #   → DuckDuckGo search integration
│   └── gemini_service.py        #   → Google Gemini API wrapper
│
├── utils/                       # 🛠 Shared utilities
│   ├── __init__.py
│   ├── config.py                #   → Environment config loader (.env)
│   └── helpers.py               #   → Timestamp & report formatting
│
├── data/                        # 📂 Auto-created at runtime
│   └── history.json             #   → Cached verification results
│
└── test_api.py                  # 🧪 DuckDuckGo search test script
```

---

## ✅ Prerequisites

- **Python 3.10** or higher
- **pip** (Python package manager)
- **Google Gemini API Key** — Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Google Fact Check API Key** *(optional)* — From [Google Cloud Console](https://console.cloud.google.com/)
- Internet connection (for DuckDuckGo search and Gemini API calls)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Syedsameer-10/RumourAgent.git
cd RumourAgent
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Version | Purpose |
|---|---|---|
| `requests` | ≥ 2.31.0 | HTTP requests to Gemini API |
| `python-dotenv` | ≥ 1.0.0 | Load `.env` configuration |
| `ddgs` | ≥ 7.0.0 | DuckDuckGo search (no API key needed) |

---

## 🔑 Configuration

### 4. Create a `.env` File

Create a file named `.env` in the project root directory:

```bash
# Windows (PowerShell)
New-Item -Path .env -ItemType File

# macOS / Linux
touch .env
```

### 5. Add Your API Keys

Open `.env` in a text editor and add:

```env
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

> **⚠️ Important:**
> - The `GEMINI_API_KEY` is **required** — it powers the AI reasoning.
> - The `GOOGLE_FACTCHECK_API_KEY` is loaded but **not actively used** in the current version (DuckDuckGo is used for evidence retrieval instead).
> - **Never commit your `.env` file to version control.** It's already in `.gitignore`.

---

## ▶️ How to Run

### Start TruthLens

```bash
python main.py
```

You'll see the TruthLens banner:

```
╔════════════════════════════════════════════════════╗
║                                                    ║
║              🔍  T R U T H L E N S  🔍             ║
║                                                    ║
║        AI-Powered Rumour Verification Agent         ║
║                                                    ║
╚════════════════════════════════════════════════════╝
```

### Interactive Terminal Loop

Once running, you can type any claim or rumour to verify. The agent pipeline processes it and prints a verification report.

**To exit:** Type `quit`, `exit`, or `q` at the prompt.

---

## 💡 Usage Examples

### Example 1 — Verifying a False Claim

```
🔍 Enter a claim to verify: COVID vaccines contain microchips

═══════════════════════════════════════════════════════

  Claim:
  COVID vaccines contain microchips

  Verdict:      ❌ False
  Confidence:   95%

  Explanation:
  Multiple fact-checking organizations including Snopes,
  PolitiFact, and Reuters have debunked this claim. COVID-19
  vaccines contain mRNA or viral vector components and do
  not contain any tracking or microchip devices.

  Source:       reuters.com
  URL:          https://www.reuters.com/...

═══════════════════════════════════════════════════════
```

### Example 2 — Verifying a True Claim

```
🔍 Enter a claim to verify: The Earth revolves around the Sun

═══════════════════════════════════════════════════════

  Claim:
  The Earth revolves around the Sun

  Verdict:      ✅ True
  Confidence:   99%

  Explanation:
  This is a well-established scientific fact confirmed by
  centuries of astronomical observation and research.

═══════════════════════════════════════════════════════
```

### Example 3 — Testing DuckDuckGo Search (Standalone)

```bash
python test_api.py
```

This runs a standalone test to verify that DuckDuckGo search is working:

```
Searching: covid vaccine contains microchip fact check

Got 3 results:

1. Title: Fact Check: COVID Vaccines Do Not Contain Microchips
   URL: https://www.reuters.com/...
```

---

## ⚙️ How It Works

### Step-by-Step Pipeline

| Step | Agent / Service | Action |
|---|---|---|
| 1 | **ClaimAgent** | Strips whitespace, collapses spaces, normalizes text to lowercase |
| 2 | **MemoryAgent** (lookup) | Searches `data/history.json` for a matching cached claim |
| 3 | **EvidenceAgent** → `FactCheckService` | Appends "fact check" to the claim and searches DuckDuckGo for 5 results |
| 4 | **ReasoningAgent** → `GeminiService` | Sends the claim + evidence to Gemini 2.5 Flash for analysis |
| 5 | **MemoryAgent** (save) | Saves the verdict, confidence, explanation, and timestamp to `history.json` |
| 6 | **print_report()** | Displays a formatted verification report in the terminal |

### Service Layer Details

| Service | External API | Key Required? | Purpose |
|---|---|---|---|
| `FactCheckService` | DuckDuckGo Search (`ddgs`) | ❌ No | Finds fact-check articles from the web |
| `GeminiService` | Google Gemini 2.5 Flash | ✅ Yes (`GEMINI_API_KEY`) | Analyzes evidence and produces structured verdicts |

---

## 🧱 Design Principles

| Principle | Implementation |
|---|---|
| **Single Responsibility** | Each agent handles exactly one task (clean, cache, search, reason) |
| **Service Layer Abstraction** | Agents never call external APIs directly — they use injected service objects |
| **Dependency Injection** | Services are instantiated in `main.py` and passed to agents at construction time |
| **Caching** | MemoryAgent stores results in a local JSON file to prevent duplicate API calls |
| **Extensibility** | Modular architecture supports future additions (web UI, multi-source, analytics) without restructuring |
| **Graceful Degradation** | GeminiService returns a safe default result on API errors, timeouts, or connection failures |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'ddgs'` | Run `pip install ddgs>=7.0.0` |
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install python-dotenv>=1.0.0` |
| Gemini API returns errors | Verify your `GEMINI_API_KEY` in `.env` is valid and has quota remaining |
| No search results found | Check your internet connection; DuckDuckGo may rate-limit excessive requests |
| `FileNotFoundError` for `.env` | Ensure the `.env` file is in the project root (same directory as `main.py`) |
| Python version errors | Ensure Python ≥ 3.10 with `python --version` |

---

## 📊 Technology Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **AI Model** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Web Search** | DuckDuckGo (via `ddgs` library) |
| **HTTP Client** | `requests` |
| **Config Management** | `python-dotenv` |
| **Data Storage** | Local JSON file (`data/history.json`) |
| **Interface** | Terminal / CLI |

---

## 🗺 Roadmap (Future Phases)

- [ ] 🌐 Web-based frontend (Flask / Streamlit)
- [ ] 📡 Multi-source evidence retrieval (Google Fact Check API, NewsAPI)
- [ ] 📈 Analytics dashboard for verification trends
- [ ] 🔄 Real-time social media monitoring
- [ ] 🧠 Enhanced reasoning with multi-model consensus

---

## 📄 License

This project is open source. See the repository for license details.

---

<div align="center">

**Built with ❤️ by [Syedsameer-10](https://github.com/Syedsameer-10)**

🔍 *Fighting misinformation, one claim at a time.*

</div>
]]>
