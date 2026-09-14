from skill_quest import config
from langchain.agents import create_agent

from skill_quest.ladder.models import LadderInput, Ladder
from skill_quest.ladder.prompts import ladder_architect_prompt
from skill_quest.llm import robust_model

agent = create_agent(
    model=robust_model,
    middleware=[ladder_architect_prompt],
    context_schema=LadderInput,
    response_format=Ladder,
)
