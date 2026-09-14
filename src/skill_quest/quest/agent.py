from skill_quest import config
from langchain.agents import create_agent

from skill_quest.llm import robust_model
from skill_quest.quest.models import QuestDesignInput, QuestSet
from skill_quest.quest.prompts import quest_designer_prompt

agent = create_agent(
    model=robust_model,
    middleware=[quest_designer_prompt],
    context_schema=QuestDesignInput,
    response_format=QuestSet,
)
