from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)


from experiments.models import (
    SkillGoal,
    SkillDossier,
    Milestone,
    Capability,
    SourceRecord,
    CapabilityMap,
    QuestSet,
    MilestoneSet,
)
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Load artifacts ----------

goal_json = load_json(SkillGoal, "goal.json")
capability_map_json = load_json(CapabilityMap, "capability_map.json")
skill_dossier_json = load_json(SkillDossier, "skill_dossier.json")
milestone_set_json = load_json(MilestoneSet, "milestone_set.json")

# ---------- Input schema ----------

selected_milestone = next(
    milestone
    for milestone in milestone_set_json.milestones
    if milestone.id == "ms-02-two-position-pentatonic"
)

class QuestDesignInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    milestone: Milestone = Field(default_factory=lambda: selected_milestone)
    capabilities: list[Capability] = Field(default_factory=lambda: capability_map_json.capabilities)
    sources: list[SourceRecord] = Field(default_factory=lambda: skill_dossier_json.sources)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def quest_designer_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    _goal = ctx.goal
    _milestone = ctx.milestone
    _capabilities = ctx.capabilities
    _sources = ctx.sources

    return f"""
You are the Quest Designer.

Your job is to write missions that help the player pass one milestone.

Goal:
{_goal}

Milestone:
{_milestone}

Capabilities:
{_capabilities}

Sources:
{_sources}

Generate exactly 5 Quest objects for this milestone:
- 3 drill quests
- 1 world, social, discovery, or creation quest
- exactly 1 demonstration quest

Every quest MUST contain every field in the Quest schema, including:
- id
- milestone_id
- quest_type
- title
- purpose
- instructions
- estimated_days
- sessions
- minutes_per_session
- success_criteria
- evidence_required
- resource_url
- resource_reason
- twist
- failure_route
- optional

For every quest:
- milestone_id must be exactly "{_milestone.id}"
- estimated_days must be at least 1
- sessions must be at least 1
- minutes_per_session must be greater than 0
- success_criteria must be observable
- failure_route must describe the next action if the learner does not pass
- do not omit fields
- use null for optional resource_url, resource_reason, or twist when no value is needed
- do not use Markdown links
- resource_url must be a plain URL beginning with "https://"
- resource_reason must be a plain sentence
- return exactly 5 quest objects, not 4 and not 6
- do not add any text outside the structured QuestSet

The demonstration quest must:
- have quest_type "demonstration"
- directly test the milestone demonstration gate
- include evidence appropriate to the gate
- include explicit pass-oriented success criteria

Do not:
- include reflection prompts
- generate journaling
- generate daily session plans
- create unsupported technical claims
- use self-report as the only evidence for a demonstration

Return only the structured QuestSet object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[quest_designer_prompt],
    context_schema=QuestDesignInput,
    response_format=QuestSet,
)
