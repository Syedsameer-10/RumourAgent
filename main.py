"""
TruthLens — AI-Powered Rumour Verification Agent

Main orchestration module. Initializes all services and agents,
runs the terminal-based verification loop, and coordinates the
agent pipeline:

    User Input → ClaimAgent → MemoryAgent (lookup) → EvidenceAgent
    → ReasoningAgent → MemoryAgent (save) → Print Report
"""

import sys
import logging

from utils.config import Config
from utils.helpers import print_report, TerminalSpinner

from services.factcheck_service import FactCheckService
from services.gemini_service import GeminiService

from agents.claim_agent import ClaimAgent
from agents.memory_agent import MemoryAgent
from agents.evidence_agent import EvidenceAgent
from agents.reasoning_agent import ReasoningAgent

# ── Logging Configuration ──────────────────────────────────────────

log_level = logging.DEBUG if "--debug" in sys.argv else logging.WARNING
logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("truthlens")


# ── Banner ──────────────────────────────────────────────────────────

BANNER = """
╔════════════════════════════════════════════════════╗
║                                                    ║
║              🔍  T R U T H L E N S  🔍             ║
║                                                    ║
║        AI-Powered Rumour Verification Agent         ║
║                                                    ║
╚════════════════════════════════════════════════════╝
"""


def initialize() -> tuple[ClaimAgent, MemoryAgent, EvidenceAgent, ReasoningAgent]:
    """
    Initialize configuration, services, and agents.
    """
    config = Config()
    config.validate()

    factcheck_service = FactCheckService(api_key=config.google_factcheck_api_key)
    gemini_service = GeminiService(api_key=config.gemini_api_key)

    claim_agent = ClaimAgent()
    memory_agent = MemoryAgent(history_file=config.history_file)
    evidence_agent = EvidenceAgent(factcheck_service=factcheck_service)
    reasoning_agent = ReasoningAgent(gemini_service=gemini_service)

    logger.info("All agents initialized successfully.")
    return claim_agent, memory_agent, evidence_agent, reasoning_agent


def verify_claim(
    raw_input: str,
    claim_agent: ClaimAgent,
    memory_agent: MemoryAgent,
    evidence_agent: EvidenceAgent,
    reasoning_agent: ReasoningAgent,
) -> None:
    """
    Run the verification pipeline for a single rumour.

    Features:
    - Consistent cache check before external calls
    - Allows '!<claim>' prefix or '--fresh' CLI flag to force live re-verification
    - Only caches valid successful results
    """
    # Check if user requested a forced fresh lookup
    force_fresh = raw_input.startswith("!") or "--fresh" in sys.argv
    cleaned_input = raw_input[1:].strip() if raw_input.startswith("!") else raw_input

    # Step 1: Normalize the claim
    claim = claim_agent.process(cleaned_input)
    if not claim:
        print("\n  ⚠  Please enter a valid claim to verify.\n")
        return

    # Step 2: Check Cache (if not forced fresh)
    if not force_fresh:
        cached_result = memory_agent.search(claim)
        if cached_result:
            print("\n  📋  [CACHE HIT] Found previous verification result (type '!<claim>' to force re-check):")
            print_report(cached_result)
            return

    # Step 3: Gather live evidence from web & fact-check sources
    with TerminalSpinner("Searching official fact-checks & multi-source web evidence"):
        evidence = evidence_agent.gather(claim)

    # Step 4: Analyze and produce grounded verdict with Gemini 2.5 Flash
    with TerminalSpinner("Analyzing evidence & generating grounded verdict with Gemini 2.5 Flash"):
        result = reasoning_agent.analyze(claim, evidence)

    # Step 5: Save to memory (Only caches valid results; operational failures are ignored by MemoryAgent)
    if result.get("status") == "SUCCESS":
        memory_agent.save(result)

    # Step 6: Print formatted report
    print_report(result)


def main() -> None:
    """Main entry point — run the terminal-based verification loop."""
    print(BANNER)

    try:
        claim_agent, memory_agent, evidence_agent, reasoning_agent = initialize()
    except ValueError as e:
        print(f"\n  ❌  Configuration Error: {e}")
        print("  Please update your .env file and try again.\n")
        sys.exit(1)
    except Exception as e:
        logger.exception("Failed to initialize TruthLens.")
        print(f"\n  ❌  Initialization Error: {e}\n")
        sys.exit(1)

    print("  Type a rumour to verify, or 'quit' to exit.")
    print("  Tip: Prefix with '!' (e.g., '!earth is round') to bypass cache and re-verify live.\n")

    while True:
        try:
            user_input = input("  🔍  Enter rumour: ").strip()

            if user_input.lower() in ("quit", "exit", "q"):
                print("\n  👋  Goodbye! Stay truthful.\n")
                break

            if not user_input:
                continue

            verify_claim(
                raw_input=user_input,
                claim_agent=claim_agent,
                memory_agent=memory_agent,
                evidence_agent=evidence_agent,
                reasoning_agent=reasoning_agent,
            )

        except KeyboardInterrupt:
            print("\n\n  👋  Goodbye! Stay truthful.\n")
            break
        except Exception as e:
            logger.exception("Error during verification.")
            print(f"\n  ❌  An error occurred: {e}\n")


if __name__ == "__main__":
    main()
