from skill_quest import config

from langchain.agents import create_agent

from skill_quest.goal.models import GoalInput, SkillGoal
from skill_quest.goal.prompts import goal_prompt
from skill_quest.llm import robust_model

agent = create_agent(
    model=robust_model,
    middleware=[goal_prompt],
    context_schema=GoalInput,
    response_format=SkillGoal,
)
