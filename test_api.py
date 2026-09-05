"""Test ddgs search directly."""
from ddgs import DDGS

ddgs = DDGS()
query = "covid vaccine contains microchip fact check"
print(f"Searching: {query}\n")

try:
    results = ddgs.text(keywords=query, max_results=3)
    print(f"Got {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.get('title', 'N/A')}")
        print(f"   URL: {r.get('href', 'N/A')}")
        print(f"   Snippet: {r.get('body', 'N/A')[:100]}...")
        print()
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
