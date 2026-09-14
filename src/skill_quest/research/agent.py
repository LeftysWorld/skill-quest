from skill_quest import config

from langchain.agents import create_agent

from .models import ResearchInput, SkillDossier
from .prompts import research_prompt
from .tools import web_search
from ..llm import robust_model

agent = create_agent(
    model=robust_model,
    tools=[web_search],
    middleware=[research_prompt],
    context_schema=ResearchInput,
    response_format=SkillDossier,
)
