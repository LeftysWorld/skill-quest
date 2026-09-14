from skill_quest import config
from langchain.agents import create_agent

from skill_quest.llm import robust_model
from skill_quest.milestone.models import MilestoneDesignInput, MilestoneSet
from skill_quest.milestone.prompts import milestone_designer_prompt

agent = create_agent(
    model=robust_model,
    middleware=[milestone_designer_prompt],
    context_schema=MilestoneDesignInput,
    response_format=MilestoneSet,
)
