"""
TruthLens Helper Utilities

Shared utility functions used across the project.
"""

from datetime import datetime, timezone


def get_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def print_report(result: dict) -> None:
    """
    Print a structured verification report to the terminal.

    Args:
        result: Dictionary containing verification results with keys:
                claim, verdict, confidence, explanation, publisher, source_url
    """
    separator = "═" * 52

    print(f"\n{separator}")
    print()
    print(f"  Claim:")
    print(f"  {result.get('claim', 'N/A')}")
    print()
    print(f"  Verdict:")
    print(f"  {result.get('verdict', 'N/A')}")
    print()
    print(f"  Confidence:")
    print(f"  {result.get('confidence', 'N/A')}%")
    print()
    print(f"  Explanation:")

    # Word-wrap explanation for clean terminal output
    explanation = result.get("explanation", "N/A")
    _print_wrapped(explanation, indent=2, width=48)

    print()
    print(f"  Publisher:")
    print(f"  {result.get('publisher', 'N/A')}")
    print()
    print(f"  Source URL:")
    print(f"  {result.get('source_url', 'N/A')}")
    print()
    print(separator)
    print()


def _print_wrapped(text: str, indent: int = 2, width: int = 48) -> None:
    """Print text with word wrapping and indentation."""
    prefix = " " * indent
    words = text.split()
    line = prefix

    for word in words:
        if len(line) + len(word) + 1 > width + indent:
            print(line)
            line = prefix + word
        else:
            if line == prefix:
                line += word
            else:
                line += " " + word

    if line.strip():
        print(line)
