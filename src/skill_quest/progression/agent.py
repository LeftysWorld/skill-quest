from skill_quest import config

from langchain.agents import create_agent

from skill_quest.progression.models import ProgressionInput, ProgressionPlan
from skill_quest.progression.prompts import progression_planner_prompt

agent = create_agent(
    model="gpt-5-nano",
    middleware=[progression_planner_prompt],
    context_schema=ProgressionInput,
    response_format=ProgressionPlan,
)
