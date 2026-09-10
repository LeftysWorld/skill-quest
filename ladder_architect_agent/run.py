import os
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from graph import graph

FERMENTATION_TEMPLATE = """
Six tiers:
0 Culture (buy starter from person)
1 First batch
2 Tracks (Bottle, Grain, Koji, Orchard)
3 World nodes (brewery/club visit)
4 Long ones (miso, sake)
5 Give it away
"""

state = {
    "skill": "fermentation",
    "ladder_template": FERMENTATION_TEMPLATE,
}

result = graph.invoke(state)
print(result.get("draft_quests", []))

