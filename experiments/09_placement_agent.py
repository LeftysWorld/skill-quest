'''
Responsibility
Place a learner on the ladder.

For the skeleton, use:

self-report;

optional baseline notes;

manually supplied evidence status.

Do not build a sophisticated placement assessment yet.

Move-on gate
The Placement Agent is ready when it can:

recommend a start point;

distinguish demonstrated from unverified;

explain its confidence;

avoid putting every learner at the same starting point.


'''

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from models import SkillGoal, Ladder, Capability

from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Input schema ----------

class PlacementInput(BaseModel):
    goal: SkillGoal
    ladder: Ladder
    capabilities: list[Capability]
    learner_description: str


# ---------- Output schema ----------

class Placement(BaseModel):
    starting_milestone_id: str
    demonstrated_capability_ids: list[str]
    unverified_capability_ids: list[str]
    rationale: str
    confidence: float


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def placement_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    goal = ctx.goal
    ladder = ctx.ladder
    capabilities = ctx.capabilities
    learner_description = ctx.learner_description

    return f"""
You are the Placement Agent.

Your job is to find where the player already is on the ladder.

Skill goal:
{goal}

Ladder:
{ladder}

Capabilities:
{capabilities}

Learner description:
{learner_description}

Produce a Placement that:
- selects a starting_milestone_id from the ladder
- lists demonstrated_capability_ids (what the learner can already do)
- lists unverified_capability_ids (claimed but not demonstrated)
- provides a rationale for the placement
- provides a confidence score (0–1)

Do not:
- place every learner at the same starting point
- treat self-report as demonstrated capability
- invent capabilities that are not in the capability list

Return only the requested Placement object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[placement_prompt],
    context_schema=PlacementInput,
    response_format=Placement,
)
