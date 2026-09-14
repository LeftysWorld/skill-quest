from skill_quest import config
from langchain.agents import create_agent

from skill_quest.capability.models import (
    CapabilityMap,
    CapabilityMappingInput,
)
from skill_quest.capability.prompts import capability_mapper_prompt


agent = create_agent(
    model="gpt-5-nano",
    middleware=[capability_mapper_prompt],
    context_schema=CapabilityMappingInput,
    response_format=CapabilityMap,
)
