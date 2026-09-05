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
from utils.helpers import print_report

from services.factcheck_service import FactCheckService
from services.gemini_service import GeminiService

from agents.claim_agent import ClaimAgent
from agents.memory_agent import MemoryAgent
from agents.evidence_agent import EvidenceAgent
from agents.reasoning_agent import ReasoningAgent

# ── Logging Configuration ──────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
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

    Returns:
        A tuple of (ClaimAgent, MemoryAgent, EvidenceAgent, ReasoningAgent).
    """
    # Load and validate configuration
    config = Config()
    config.validate()

    # Initialize services
    factcheck_service = FactCheckService(api_key=config.google_factcheck_api_key)
    gemini_service = GeminiService(api_key=config.gemini_api_key)

    # Initialize agents with dependency injection
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
    Run the full verification pipeline for a single rumour.

    Flow:
        1. ClaimAgent normalizes the input
        2. MemoryAgent checks for a cached result
        3. If cached → print and return
        4. EvidenceAgent gathers fact-check evidence
        5. ReasoningAgent analyzes evidence and produces verdict
        6. MemoryAgent saves the new result
        7. Print the verification report

    Args:
        raw_input: Raw rumour text from the user.
        claim_agent: The ClaimAgent instance.
        memory_agent: The MemoryAgent instance.
        evidence_agent: The EvidenceAgent instance.
        reasoning_agent: The ReasoningAgent instance.
    """
    # Step 1: Normalize the claim
    claim = claim_agent.process(raw_input)
    if not claim:
        print("\n  ⚠  Please enter a valid claim to verify.\n")
        return

    # Step 2: Check memory for cached result
    cached_result = memory_agent.search(claim)
    if cached_result:
        print("\n  📋  Found cached verification result:")
        print_report(cached_result)
        return

    # Step 3: Gather evidence
    print("\n  🔎  Searching for fact-check evidence...")
    evidence = evidence_agent.gather(claim)

    if not evidence:
        print("  ⚠  No fact-check evidence found. Proceeding with AI analysis...")

    # Step 4: Analyze and produce verdict
    print("  🤖  Analyzing evidence with AI...")
    result = reasoning_agent.analyze(claim, evidence)

    # Step 5: Save to memory
    memory_agent.save(result)

    # Step 6: Print the report
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

    print("  Type a rumour to verify, or 'quit' to exit.\n")

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
