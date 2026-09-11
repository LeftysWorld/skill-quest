from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import SkillGoal, SkillDossier, CapabilityMap
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Load goal json ----------

goal_json = load_json(SkillGoal, "goal.json")
skill_dossier_json = load_json(SkillDossier, "skill_dossier.json")

# ---------- Input schema ----------

class CapabilityMappingInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    dossier: SkillDossier = Field(default_factory=lambda: skill_dossier_json)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def capability_mapper_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    _goal = ctx.goal
    _dossier = ctx.dossier

    return f"""
You are the Capability Mapper.

Your job is to convert the research dossier into observable learner capabilities.

Skill goal:
{_goal}

Skill dossier:
{_dossier}

Produce a CapabilityMap that:
- lists 20–60 capabilities a learner can observably do
- gives each capability:
  - a name and description
  - a category (knowledge, technique, timing, perception, judgment, creativity, communication, transfer)
  - observable behaviors
  - prerequisite_ids referencing other capabilities
  - evidence_types (audio, video, photo, note, witness, reading, gps)
  - a tier_hint (0–5)
  - optional estimated_days_at_30_min
  - common failure modes
  - a confidence score

Do not:
- create quests, sessions, or practice plans
- define capabilities only as topics or lessons
- invent prerequisites that contradict the dossier

Return only the requested CapabilityMap object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[capability_mapper_prompt],
    context_schema=CapabilityMappingInput,
    response_format=CapabilityMap,
)
