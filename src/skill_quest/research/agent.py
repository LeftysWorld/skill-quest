from skill_quest import config

from langchain.agents import create_agent

from .models import ResearchInput, SkillDossier
from .prompts import research_prompt
from .tools import web_search

agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    middleware=[research_prompt],
    context_schema=ResearchInput,
    response_format=SkillDossier,
)
