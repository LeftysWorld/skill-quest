'''
Responsibility
The Progression Router is the first genuinely stateful decision agent.

It decides:

text
Passed:
→ advance to next milestone.

Partial:
→ generate one targeted remediation quest.

Failed:
→ retry with a smaller or easier target.

Insufficient evidence:
→ request a better submission.

Plateau:
→ change method, route, or track.
It then passes next_quest_requirements to the Quest Designer.

Move-on gate
The Progression Router is ready when it can produce different actions for:

pass;

partial;

fail;

insufficient evidence;

repeated failure.
'''

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from models import Milestone, Ladder, Quest, Assessment

from typing import Any, Literal
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Input schema ----------

class ProgressionInput(BaseModel):
    ladder: Ladder
    milestones: list[Milestone]
    quests: list[Quest]
    assessment: Assessment
    player_model: dict[str, Any]


# ---------- Output schema ----------

class ProgressionDecision(BaseModel):
    action: Literal[
        "advance",
        "retry",
        "remediate",
        "branch",
        "pause",
        "rest",
    ]
    target_milestone_id: str | None
    target_capability_ids: list[str]
    rationale: str
    next_quest_requirements: list[str]
    player_model_updates: dict[str, Any]


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def progression_router_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    ladder = ctx.ladder
    milestones = ctx.milestones
    assessment = ctx.assessment
    player_model = ctx.player_model

    return f"""
You are the Progression Router. This is the game master.

Your job is to decide what happens after a verdict.

Ladder:
{ladder}

Milestones:
{milestones}

Assessment:
{assessment}

Player model:
{player_model}

Produce a ProgressionDecision that:
- sets action to "advance", "retry", "remediate", "branch", "pause", or "rest"
- sets current_milestone_id
- optionally sets target_milestone_id
- lists target_capability_ids
- provides a rationale
- lists next_quest_requirements (what the next quest must target)
- provides player_model_updates (capability scores, confidence, recurring gaps, etc.)

Apply these rules:
- if passed, usually advance
- if partial, usually remediate with a targeted drill
- if failed, usually retry with a smaller or easier target
- if insufficient_evidence, request better evidence
- detect plateaus (three fails on one milestone) and consider branch or method change
- detect boredom (fast drill completion, skipped world quests) and increase transfer

Do not:
- generate quests directly (that is the Quest Designer's job)
- ignore the assessment status

Return only the requested ProgressionDecision object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[progression_router_prompt],
    context_schema=ProgressionInput,
    response_format=ProgressionDecision,
)
