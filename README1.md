# 🔍 TruthLens — AI-Powered Rumour Verification Agent

TruthLens is a modular, agent-based rumour verification system that uses multiple AI agents working in sequence to verify claims against trusted sources.

---

## 🤖 AI Model

| Property | Details |
| --- | --- |
| **Model Name** | `gemini-2.5-flash` |
| **Full Model ID** | `models/gemini-2.5-flash` |
| **Provider** | Google — Generative Language API |
| **API Endpoint** | `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent` |
| **Temperature** | `0.3` |
| **Max Output Tokens** | `2048` |
| **Response Format** | `application/json` (structured JSON output) |
| **Use in TruthLens** | Analyzes fact-check evidence and returns a verdict (`True` / `False` / `Partially True` / `Unverified`), a confidence score (0–100), and a detailed explanation |

---

## 🏗 Architecture

```
User Input
    ↓
ClaimAgent        → Normalizes and cleans the input
    ↓
MemoryAgent       → Checks for cached verifications
    ↓
EvidenceAgent     → Retrieves fact-check evidence (DuckDuckGo Search)
    ↓
ReasoningAgent    → Analyzes evidence and produces verdict (Gemini 2.5 Flash)
    ↓
MemoryAgent       → Saves the verification result
    ↓
Verification Report
```

### Design Principles

- **Single Responsibility** — Each agent does exactly one thing.
- **Service Layer Abstraction** — Agents never call external APIs directly — they use injected services.
- **Dependency Injection** — Services are passed into agents at construction time.
- **Extensible** — The architecture is ready for future phases (frontend, multi-source, analytics) without restructuring.

---

## 📁 Project Structure

```
truthlens/
├── main.py                  # Orchestration and terminal interface
├── agents/
│   ├── claim_agent.py       # Input normalization
│   ├── evidence_agent.py    # Evidence retrieval
│   ├── memory_agent.py      # Verification caching
│   └── reasoning_agent.py   # Verdict generation
├── services/
│   ├── factcheck_service.py # DuckDuckGo fact-check search wrapper
│   └── gemini_service.py    # Google Gemini 2.5 Flash API wrapper
├── utils/
│   ├── config.py            # Environment variable loading
│   └── helpers.py           # Shared utilities
├── data/
│   └── history.json         # Verification cache (auto-created)
├── .env                     # API keys (not committed)
├── requirements.txt         # Python dependencies
└── README.md
```

---

## ⚙️ Setup

### 1. Clone and Install

```bash
git clone https://github.com/Syedsameer-10/RumourAgent.git
cd RumourAgent
pip install -r requirements.txt
```

#### Dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| `requests` | ≥ 2.31.0 | HTTP client for Gemini API calls |
| `python-dotenv` | ≥ 1.0.0 | Loads API keys from `.env` file |
| `ddgs` | ≥ 7.0.0 | DuckDuckGo search (no API key required) |

### 2. Configure API Keys

Create a `.env` file in the project root and add your API keys:

```env
GOOGLE_FACTCHECK_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

| Key | Required | Where to Get |
| --- | --- | --- |
| `GEMINI_API_KEY` | ✅ Yes | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GOOGLE_FACTCHECK_API_KEY` | ❌ Optional | [Google Cloud Console](https://console.cloud.google.com/) |

> **Note:** The current version uses DuckDuckGo for evidence search (no key needed). The `GOOGLE_FACTCHECK_API_KEY` is loaded for future multi-source support.

### 3. Run

```bash
python main.py
```

Enter a rumour when prompted. Type `quit` or `exit` to stop.

---

## 💡 Usage

### Example Output

```
════════════════════════════════════════════════════

  Claim:
  covid vaccine contains microchips

  Verdict:
  False

  Confidence:
  95%

  Explanation:
  Multiple fact-checking organizations have debunked this claim.
  There is no scientific evidence supporting the presence of
  microchips in COVID-19 vaccines.

  Publisher:
  PolitiFact

  Source URL:
  https://www.politifact.com/...

════════════════════════════════════════════════════
```

---

## 🔄 How It Works

| Step | Component | What It Does |
| --- | --- | --- |
| 1 | **ClaimAgent** | Strips whitespace, collapses spaces, lowercases the input |
| 2 | **MemoryAgent** | Looks up `data/history.json` for a cached result |
| 3 | **EvidenceAgent** → `FactCheckService` | Searches DuckDuckGo with `"<claim> fact check"` and returns top 5 results |
| 4 | **ReasoningAgent** → `GeminiService` | Sends claim + evidence to **Gemini 2.5 Flash** and receives a structured JSON verdict |
| 5 | **MemoryAgent** | Saves the result (claim, verdict, confidence, explanation, timestamp) to `history.json` |
| 6 | `print_report()` | Renders a formatted verification report in the terminal |

---

## 🛠 Tech Stack

| Layer | Technology |
| --- | --- |
| **Language** | Python 3.10+ |
| **AI Model** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Evidence Search** | DuckDuckGo (`ddgs` library — no API key) |
| **HTTP Client** | `requests` |
| **Config** | `python-dotenv` (`.env` file) |
| **Storage** | Local JSON (`data/history.json`) |
| **Interface** | Terminal / CLI |

---

## 🗺 Future Roadmap

- [ ] Streamlit frontend
- [ ] Multi-source verification (news APIs, web search)
- [ ] Enhanced reasoning with chain-of-thought
- [ ] Analytics dashboard
- [ ] Persistent database storage

---

## 📄 License

This project is open source. See the repository for license details.
