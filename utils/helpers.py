"""
TruthLens Helper Utilities

Shared utility functions used across the project with beautiful terminal output.
"""

import sys
import time
import threading
from datetime import datetime, timezone


def get_timestamp() -> str:
    """Return current UTC timestamp in readable format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class TerminalSpinner:
    """Interactive animated spinner for terminal operations."""

    def __init__(self, message: str = "Processing") -> None:
        self.message = message
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self._thread: threading.Thread | None = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.stop(success=False)
        else:
            self.stop(success=True)

    def start(self) -> None:
        self.running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self) -> None:
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r  \033[96m{frame}\033[0m  {self.message}...")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1

    def stop(self, success: bool = True) -> None:
        if not self.running:
            return
        self.running = False
        if self._thread:
            self._thread.join()
        
        status_icon = "\033[92m✔\033[0m" if success else "\033[91m✖\033[0m"
        sys.stdout.write(f"\r  {status_icon}  {self.message} (done)   \n")
        sys.stdout.flush()


def print_report(result: dict) -> None:
    """
    Print an aesthetically formatted verification report in the terminal.

    Args:
        result: Dictionary containing verification results.
    """
    status = result.get("status", "SUCCESS")
    verdict = result.get("verdict", "Unverified").strip()
    confidence = result.get("confidence", 0)
    claim = result.get("claim", "N/A")
    explanation = result.get("explanation", "N/A")
    citations = result.get("citations", [])
    model_used = result.get("model_used", "gemini-2.5-flash")
    verified_at = result.get("verified_at", get_timestamp())

    # Styling colors for terminal
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    DIM = "\033[2m"
    YELLOW = "\033[93m"

    if status == "OPERATIONAL_FAILURE":
        v_color = "\033[91m"  # Red
        badge = f"  ✖  SYSTEM FAILURE ({result.get('error_type', 'API ERROR')})  "
    elif verdict.lower() in ("true", "verified true"):
        v_color = "\033[92m"  # Green
        badge = "  ✅  TRUE  "
    elif verdict.lower() in ("false", "fake", "debunked"):
        v_color = "\033[91m"  # Red
        badge = "  ❌  FALSE  "
    elif verdict.lower() in ("misleading", "partially true"):
        v_color = "\033[93m"  # Yellow
        badge = "  ⚠️  MISLEADING / PARTIALLY TRUE  "
    else:
        v_color = "\033[95m"  # Magenta
        badge = "  ❓  UNVERIFIED  "

    try:
        conf_num = int(confidence)
    except (ValueError, TypeError):
        conf_num = 0
    clamped_conf = max(0, min(100, conf_num))
    filled = int(clamped_conf / 10)
    bar = "█" * filled + "░" * (10 - filled)

    width = 68
    horiz = "─" * width

    print(f"\n{CYAN}┌{horiz}┐{RESET}")
    print(f"{CYAN}│{RESET}  {BOLD}TRUTHLENS VERIFICATION REPORT{RESET}".ljust(width + 8) + f"{CYAN}│{RESET}")
    print(f"{CYAN}├{horiz}┤{RESET}")

    # Claim
    print(f"{CYAN}│{RESET}  {DIM}CLAIM:{RESET}")
    _print_boxed_wrapped(claim, width=width, indent=4)
    print(f"{CYAN}│{RESET}")

    if status == "OPERATIONAL_FAILURE":
        print(f"{CYAN}│{RESET}  {BOLD}STATUS:{RESET} {v_color}{BOLD}{badge}{RESET}")
        print(f"{CYAN}│{RESET}  {DIM}Error Details:{RESET} {result.get('error_message', 'Unknown failure')}")
    else:
        # Verdict & Confidence
        verdict_line = f"  {BOLD}VERDICT:{RESET} {v_color}{BOLD}{badge}{RESET}   {BOLD}CONFIDENCE:{RESET} {clamped_conf}% [{v_color}{bar}{RESET}]"
        print(f"{CYAN}│{RESET}{verdict_line}")
        print(f"{CYAN}│{RESET}")

        # Explanation
        print(f"{CYAN}│{RESET}  {BOLD}REASONING & GROUNDED EVIDENCE:{RESET}")
        _print_boxed_wrapped(explanation, width=width, indent=4)
        print(f"{CYAN}│{RESET}")

        # Citations list
        if citations:
            print(f"{CYAN}│{RESET}  {BOLD}VERIFIED CITATIONS ({len(citations)}):{RESET}")
            for cit in citations[:3]:
                pub = cit.get("publisher", "Web Source")
                tier = cit.get("tier", "Source")
                url = cit.get("url", "")
                title = cit.get("title", "")
                print(f"{CYAN}│{RESET}    • {BOLD}[{pub}]{RESET} {DIM}({tier}){RESET}")
                if title:
                    print(f"{CYAN}│{RESET}      Title: {title[:55]}...")
                if url:
                    print(f"{CYAN}│{RESET}      URL  : {url}")
        else:
            print(f"{CYAN}│{RESET}  {DIM}No direct supporting citations identified.{RESET}")

    print(f"{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {DIM}Model: {model_used} | Verified at: {verified_at}{RESET}")
    print(f"{CYAN}└{horiz}┘{RESET}\n")


def _print_boxed_wrapped(text: str, width: int = 68, indent: int = 4) -> None:
    """Print wrapped lines within the terminal box boundaries."""
    CYAN = "\033[96m"
    RESET = "\033[0m"
    max_text_len = width - indent - 4
    words = text.split()
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_text_len:
            line_str = " " * indent + current_line
            print(f"{CYAN}│{RESET}{line_str}")
            current_line = word
        else:
            current_line = f"{current_line} {word}".strip()

    if current_line:
        line_str = " " * indent + current_line
        print(f"{CYAN}│{RESET}{line_str}")
