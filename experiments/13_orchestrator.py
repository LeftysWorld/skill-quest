'''
Group 13: Orchestrator
Build the Orchestrator last as an agent, but not necessarily last as a workflow concept.

This is intentional.

If you build it first, it will hide problems in the downstream agents. If you build it last, it becomes a thin coordinator over already-working components.

Responsibility
Route Build Mode.

Route Play Mode.

Route assessment.

Decide which agent should act.

Present results to the user.

Never independently design artifacts.

Important caveat
Build the Orchestrator contract earlier, but build the actual Orchestrator agent after the specialists work.

You can begin with deterministic routing:

python
if "build" in user_message.lower():
    mode = "build"
elif "submit" in user_message.lower():
    mode = "assessment"
else:
    mode = "play"
Then replace routing logic with an agent once the workflow is stable.
'''

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from typing import Any, Literal
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# ---------- Input schema ----------

class OrchestratorInput(BaseModel):
    user_message: str
    current_mode: str | None = None
    current_state: dict[str, Any] = {}


# ---------- Output schema ----------

class OrchestratorDecision(BaseModel):
    mode: Literal["build", "play", "assessment", "placement"]
    intent: str
    agents_to_call: list[str]
    required_inputs: list[str]
    response: str


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def orchestrator_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context
    user_message = ctx.user_message
    current_mode = ctx.current_mode
    current_state = ctx.current_state

    return f"""
You are the Experience Orchestrator.

Your job is to classify intent and route to the right agents.

User message:
{user_message}

Current mode:
{current_mode}

Current state summary:
{current_state}

Produce an OrchestratorDecision that:
- sets mode to "build", "play", "assessment", or "placement"
- sets intent (e.g. "build_ladder", "generate_next_quest", "submit_result", "assess_result", "show_progress")
- lists agents_to_call (e.g. ["goal_agent", "research_agent", "capability_mapper", ...])
- lists required_inputs (e.g. ["goal", "ladder", "assessment"])
- provides a player-facing response explaining what will happen next

Routing rules:
- if the user describes an ambition and no ladder exists, use mode "build"
- if the user asks "what should I do next?" and a ladder exists, use mode "play"
- if the user submits evidence, use mode "assessment"
- if the user describes prior experience and no placement exists, use mode "placement"

Do not:
- design artifacts directly
- bypass the specialist agents
- invent state that does not exist

Return only the requested OrchestratorDecision object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[orchestrator_prompt],
    context_schema=OrchestratorInput,
    response_format=OrchestratorDecision,
)
