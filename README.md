TruthLens — AI-Powered Rumour Verification Agent
TruthLens is a modular, agent-based rumour verification system that uses multiple AI agents working in sequence to verify claims against trusted sources.

Architecture
User Input
    ↓
ClaimAgent        → Normalizes and cleans the input
    ↓
MemoryAgent       → Checks for cached verifications
    ↓
EvidenceAgent     → Retrieves fact-check evidence (Google Fact Check API)
    ↓
ReasoningAgent    → Analyzes evidence and produces verdict (Gemini API)
    ↓
MemoryAgent       → Saves the verification result
    ↓
Verification Report
Design Principles
Single Responsibility: Each agent does exactly one thing.
Service Layer Abstraction: Agents never call external APIs directly — they use injected services.
Dependency Injection: Services are passed into agents at construction time.
Extensible: The architecture is ready for future phases (frontend, multi-source, analytics) without restructuring.
Project Structure
truthlens/
├── main.py                  # Orchestration and terminal interface
├── agents/
│   ├── claim_agent.py       # Input normalization
│   ├── evidence_agent.py    # Evidence retrieval
│   ├── memory_agent.py      # Verification caching
│   └── reasoning_agent.py   # Verdict generation
├── services/
│   ├── factcheck_service.py # Google Fact Check API wrapper
│   └── gemini_service.py    # Gemini API wrapper
├── utils/
│   ├── config.py            # Environment variable loading
│   └── helpers.py           # Shared utilities
├── data/
│   └── history.json         # Verification cache (auto-created)
├── .env                     # API keys (not committed)
├── requirements.txt         # Python dependencies
└── README.md
Setup
1. Clone and install
cd truthlens
pip install -r requirements.txt
2. Configure API keys
Edit the .env file and add your API keys:

GOOGLE_FACTCHECK_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
Google Fact Check API: Enable at Google Cloud Console and create an API key.
Gemini API: Get a free key from Google AI Studio.
3. Run
python main.py
Enter a rumour when prompted. Type quit or exit to stop.

Example Output
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
Future Roadmap
Streamlit frontend
Multi-source verification (news APIs, web search)
Enhanced reasoning with chain-of-thought
Analytics dashboard
Persistent database storage
