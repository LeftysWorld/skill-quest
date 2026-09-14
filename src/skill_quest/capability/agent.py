from skill_quest import config
from langchain.agents import create_agent

from skill_quest.capability.models import (
    CapabilityMap,
    CapabilityMappingInput,
)
from skill_quest.capability.prompts import capability_mapper_prompt
from skill_quest.llm import robust_model

agent = create_agent(
    model=robust_model,
    middleware=[capability_mapper_prompt],
    context_schema=CapabilityMappingInput,
    response_format=CapabilityMap,
)
