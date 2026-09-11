from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import (
    SkillGoal,
    SkillDossier,
    ProgressionPlan,
    Milestone,
    MilestoneSet,
    SourceRecord,
    Ladder
)
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Load goal json ----------

goal_json = load_json(SkillGoal, "goal.json")
skill_dossier_json = load_json(SkillDossier, "skill_dossier.json")
progression_plan_json = load_json(ProgressionPlan, "progression_plan.json")
milestone_set_json = load_json(MilestoneSet, "milestone_set.json")

# ---------- Input schema ----------

class LadderInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    progression_plan: ProgressionPlan = Field(default_factory=lambda: progression_plan_json)
    milestones: list[Milestone] = Field(default_factory=lambda: milestone_set_json.milestones)
    sources: list[SourceRecord] = Field(default_factory=lambda: skill_dossier_json.sources)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def ladder_architect_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    _goal = ctx.goal
    _plan = ctx.progression_plan
    _milestones = ctx.milestones
    _sources = ctx.sources

    return f"""
You are the Ladder Architect.

Your job is to wire milestones into a playable tree.

Skill goal:
{_goal}

Progression plan:
{_plan}

Milestones:
{_milestones}

Sources:
{_sources}

Produce a Ladder that:
- defines id, goal_id, title, skill
- defines a north_star_capability
- selects a track_id from the progression plan
- lists alternate_track_ids
- lists milestone_ids in order
- identifies branch_points
- sets target_weeks and minutes_per_day
- lists sources and assumptions
- sets version to 1

Do not:
- write detailed quests
- change the milestone definitions
- invent tracks that contradict the progression plan

Return only the requested Ladder object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[ladder_architect_prompt],
    context_schema=LadderInput,
    response_format=Ladder,
)
