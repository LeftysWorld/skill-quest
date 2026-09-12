from skill_quest import config

from langchain.agents import create_agent

from skill_quest.goal.models import GoalInput, SkillGoal
from skill_quest.goal.prompts import goal_prompt

agent = create_agent(
    model="gpt-5-nano",
    middleware=[goal_prompt],
    context_schema=GoalInput,
    response_format=SkillGoal,
)
