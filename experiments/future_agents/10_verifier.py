'''
Phase 1 behavior
The Verifier can initially accept manually entered evidence such as:

json
{
  "evidence_type": "video",
  "duration_seconds": 180,
  "metronome_bpm": 80,
  "continuous": true,
  "mistakes": 2,
  "observed_weaknesses": [
    "Tempo accelerated during the final minute"
  ]
}
This lets you test the contract before building real media processing.

Move-on gate
The Verifier is ready when it can:

reject missing evidence;

detect incomplete submissions;

return measurements;

return weaknesses;

avoid making a progression decision.
'''

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from models import Quest

from typing import Any, Literal
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Input schema ----------

class VerificationInput(BaseModel):
    quest: Quest
    submitted_evidence: dict[str, Any]


# ---------- Output schema ----------

class Verdict(BaseModel):
    quest_id: str
    status: Literal[
        "verified",
        "incomplete",
        "pending_review",
        "rejected",
    ]
    observed_measurements: dict[str, Any] = {}
    weaknesses: list[str] = []
    confidence: float
    notes: str = ""


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def verifier_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    quest = ctx.quest
    evidence = ctx.submitted_evidence

    return f"""
You are the Verifier.

Your job is the only path to "completed."

Quest:
{quest}

Submitted evidence:
{evidence}

Produce a Verdict that:
- sets evidence_status to "verified", "incomplete", "pending_review", or "rejected"
- extracts observed_measurements from the evidence
- lists observed_strengths
- lists observed_weaknesses
- lists missing_requirements
- provides a confidence score (0–1)
- provides notes

Do not:
- accept self-rating as proof
- decide whether the milestone is passed
- invent measurements not supported by the evidence

For Phase 1, assume evidence is manually structured (duration, tempo, stops, mistakes, etc.).
Return only the requested Verdict object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[verifier_prompt],
    context_schema=VerificationInput,
    response_format=Verdict,
)
