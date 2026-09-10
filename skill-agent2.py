from dotenv import load_dotenv

from dataclasses import dataclass
from pprint import pprint
from typing import Any, Dict, Literal


from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain.messages import HumanMessage
from langchain_core.tools import tool

from tavily import TavilyClient


load_dotenv()

tavily_client = TavilyClient()


@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information."""
    return tavily_client.search(query)


@dataclass
class CurriculumContext:
    skill: str = "electric guitar"
    learner_level: Literal[
        "beginner",
        "intermediate",
        "advanced",
    ] = "beginner"
    available_minutes_per_day: int = 30
    equipment: str = (
        "electric guitar, amplifier, cable, tuner, picks, and strap"
    )


@dynamic_prompt
def curriculum_prompt(request: ModelRequest) -> str:
    context = request.runtime.context

    return f"""
You are an expert curriculum designer.

Current skill: {context.skill}
Learner level: {context.learner_level}
Available practice time: {context.available_minutes_per_day} minutes per day
Equipment: {context.equipment}

Create a beginner-to-advanced progression ladder.

Use web search when current or source-based research would improve the answer.
When you use web search, base recommendations on retrieved sources.

Return exactly 6 sequential levels. For each level, provide:

1. Level name
2. Main goal
3. Skills to learn
4. Practice activities
5. Completion condition
6. Recommended evidence of completion
7. Prerequisites

Make the progression realistic, cumulative, and safety-conscious.
"""


agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    context_schema=CurriculumContext,
    middleware=[curriculum_prompt],
)


curriculum_context = CurriculumContext(
    skill="electric guitar",
    learner_level="beginner",
    available_minutes_per_day=30,
    equipment=(
        "electric guitar, amplifier, cable, tuner, picks, and strap"
    ),
)


response = agent.invoke(
    {
        "messages": [
            HumanMessage(
                content="Create a beginner-to-advanced progression ladder."
            )
        ]
    },
    context=curriculum_context,
)


print(response)
print()
pprint(response["messages"][-1].content)
