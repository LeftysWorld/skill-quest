from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import (
    SkillGoal,
    Capability,
    CapabilityMap,
    ProgressionPlan
)
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Load goal json ----------

goal_json = load_json(SkillGoal, "goal.json")
capability_map_json = load_json(CapabilityMap, "capability_map.json")

# ---------- Input schema ----------

class ProgressionInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    capabilities: list[Capability] = Field(default_factory=lambda: capability_map_json.capabilities)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def progression_planner_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    _goal = ctx.goal
    _capabilities = ctx.capabilities

    return f"""
You are the Progression Planner.

Your job is to turn the capability graph into possible routes through the skill.

Skill goal:
{_goal}

Capabilities:
{_capabilities}

Produce a ProgressionPlan that:
- defines 2–4 tracks (directions the learner can pursue)
- for each track:
  - an id, name, identity_statement, intended_outcome
  - entry_capability_ids
  - milestone_capability_groups (clusters of capabilities per milestone)
  - optional branch_after_tier
  - exit_capability_ids
  - a rationale
- identifies shared_foundation_capability_ids used by all tracks
- identifies branch_points between tracks
- provides sequencing_rationale and pacing_rationale
- records assumptions

Do not:
- write quests or daily plans
- make tracks that differ only by arbitrary difficulty
- ignore prerequisite relationships

Return only the requested ProgressionPlan object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[progression_planner_prompt],
    context_schema=ProgressionInput,
    response_format=ProgressionPlan,
)
