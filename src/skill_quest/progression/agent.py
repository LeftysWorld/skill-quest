from skill_quest import config

from langchain.agents import create_agent

from skill_quest.llm import robust_model
from skill_quest.progression.models import ProgressionInput, ProgressionPlan
from skill_quest.progression.prompts import progression_planner_prompt


agent = create_agent(
    model=robust_model,
    middleware=[progression_planner_prompt],
    context_schema=ProgressionInput,
    response_format=ProgressionPlan,
)
