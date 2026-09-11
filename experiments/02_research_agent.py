from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import SkillGoal, SkillDossier
from experiments.helpers import load_json

from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.tools import tool

from tavily import TavilyClient
tavily_client = TavilyClient()

# ---------- Load goal json ----------

goal_json = load_json(SkillGoal, "goal.json")

# ---------- Tools ----------

@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information."""
    return tavily_client.search(query)

# ---------- Input schema ----------

class ResearchInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def research_prompt(request: ModelRequest) -> str:
    research_input: ResearchInput = request.runtime.context
    _goal = research_input.goal

    return f"""
You are the Research Agent.

Your job is to learn how the skill in the supplied goal is actually taught
before another agent designs capabilities, milestones, or quests.

Skill goal:
{_goal.model_dump_json(indent=2)}

Produce a SkillDossier that:
- describes the scope of the skill
- identifies progression patterns from credible curricula
- lists capability candidates a learner must demonstrate
- identifies prerequisite patterns
- lists common failure modes and plateaus
- identifies safety constraints
- identifies authentic contexts where the skill is used
- attaches source records
- records disagreements and uncertainties

Each source record should include:
- id
- title
- url
- source_type
- relevance
- extracted_claims
- confidence

Research rules:
- Use credible, structured curricula and expert guidance.
- Prefer multiple sources rather than one source.
- Distinguish source-supported findings from your own synthesis.
- Record uncertainty when sources disagree or evidence is thin.
- Do not invent URLs.
- Do not create quests.
- Do not create sessions.
- Do not create practice plans.
- Do not provide coaching.
- Do not provide a long explanation outside the structured output.

Return only the requested SkillDossier object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    middleware=[research_prompt],
    context_schema=ResearchInput,
    response_format=SkillDossier,
)
