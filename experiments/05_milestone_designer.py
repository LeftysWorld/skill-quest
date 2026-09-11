from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import SkillGoal, ProgressionPlan, Capability, MilestoneSet, CapabilityMap
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Load goal json ----------

goal_json = load_json(SkillGoal, "goal.json")
capability_map_json = load_json(CapabilityMap, "capability_map.json")
progression_plan_json = load_json(ProgressionPlan, "progression_plan.json")
recommended_track_id = "tp-01-foundations-pentatonic-loop"

# ---------- Input schema ----------

class MilestoneDesignInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    capabilities: list[Capability] = Field(default_factory=lambda: capability_map_json.capabilities)
    progression_plan: ProgressionPlan = Field(default_factory=lambda: progression_plan_json)
    selected_track_id: str = recommended_track_id


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def milestone_designer_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    _goal = ctx.goal
    _capabilities = ctx.capabilities
    _plan = ctx.progression_plan
    track_id = ctx.selected_track_id

    return f"""
You are the Milestone Designer.

Your job is to group capabilities into milestones a player can pass.

Skill goal:
{_goal}

Capabilities:
{_capabilities}

Progression plan:
{_plan}

Selected track id:
{track_id}

Produce a MilestoneSet that:
- defines 4–8 milestones for the selected track
- for each milestone:
  - id, track_id, tier
  - title and capability_ids
  - a capability_statement describing what the learner can do
  - why_it_matters
  - target_weeks
  - a demonstration_gate (what must be demonstrated to pass)
  - pass_criteria (observable conditions)
  - failure_routes (what happens if they fail)
  - unlocks (what this milestone enables next)
- provides a design_rationale explaining the milestone sequence

Do not:
- write detailed quests or session plans
- define milestones only as topics
- create milestones without a demonstration gate

Return only the requested MilestoneSet object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[milestone_designer_prompt],
    context_schema=MilestoneDesignInput,
    response_format=MilestoneSet,
)
