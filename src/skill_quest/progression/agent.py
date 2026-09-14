from skill_quest import config

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from skill_quest.progression.models import ProgressionInput, ProgressionPlan
from skill_quest.progression.prompts import progression_planner_prompt

model = ChatOpenAI(
    model="gpt-5-nano",
    timeout=180,
    max_retries=3,
)

agent = create_agent(
    model=model,
    middleware=[progression_planner_prompt],
    context_schema=ProgressionInput,
    response_format=ProgressionPlan,
)
