from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from pprint import pprint
from tavily import TavilyClient
from typing import Dict, Any

load_dotenv()
tavily_client = TavilyClient()


@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information"""
    return tavily_client.search(query)


skill = "electric guitar"

agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    system_prompt=f"""
You are an expert {skill} curriculum designer.

Create a beginner-to-advanced progression ladder for {skill}.

Use web search when current or source-based research would improve the answer.
When you use web search, base your recommendations on the retrieved sources.

Return exactly 6 sequential levels. For each level, provide:

1. Level name
2. Main goal
3. Skills to learn
4. Practice activities
5. Completion condition
6. Recommended evidence of completion
7. Prerequisites

Make the progression realistic, cumulative, and safety-conscious.
Do not assume the learner owns specific equipment beyond an {skill},
amplifier, cable, tuner, picks, and strap.
"""
)

response = agent.invoke({"messages": [HumanMessage(
    content="Create a beginner-to-advanced electric guitar progression ladder."
)]})

print(response)
print()
pprint(response['messages'][-1].content)

