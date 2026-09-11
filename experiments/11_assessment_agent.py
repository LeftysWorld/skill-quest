'''
Responsibility
Assessment compares the verified result against the milestone’s pass criteria.

It should not invent new quests. It should recommend a target for the Progression Router.

Move-on gate
The Assessment Agent is ready when the same verdict consistently produces:

pass when criteria are satisfied;

partial when only some criteria are satisfied;

fail when the core capability is missing;

insufficient evidence when the evidence cannot support a judgment.
'''

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from models import Milestone, Quest, Verdict

from typing import Literal
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Input schema ----------

class AssessmentInput(BaseModel):
    milestone: Milestone
    quest: Quest
    verdict: Verdict


# ---------- Output schema ----------

class Assessment(BaseModel):
    milestone_id: str
    quest_id: str
    status: Literal[
        "passed",
        "partial",
        "failed",
        "insufficient_evidence",
    ]
    score: float
    strengths: list[str]
    weaknesses: list[str]
    recommended_target: str | None = None


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def assessment_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    milestone = ctx.milestone
    quest = ctx.quest
    verdict = ctx.verdict

    return f"""
You are the Assessment Agent.

Your job is to judge verified evidence against a milestone rubric.

Milestone:
{milestone}

Quest:
{quest}

Verdict:
{verdict}

Produce an Assessment that:
- sets status to "passed", "partial", "failed", or "insufficient_evidence"
- provides a score (0–1)
- provides criterion_results mapping criterion names to results
- lists strengths and weaknesses
- identifies a limiting_gap if any
- provides a recommended_target for the Progression Router

Do not:
- contradict the verifier's observed measurements
- invent new evidence
- decide progression (that is the Progression Router's job)

Return only the requested Assessment object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[assessment_prompt],
    context_schema=AssessmentInput,
    response_format=Assessment,
)
