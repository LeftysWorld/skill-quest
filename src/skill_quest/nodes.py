from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from skill_quest.goal.agent import agent as goal_agent
from skill_quest.goal.models import GoalInput, LearnerContext, SkillGoal
from skill_quest.research.agent import agent as research_agent
from skill_quest.research.models import ResearchInput, SkillDossier
from skill_quest.capability.agent import agent as capability_agent
from skill_quest.capability.models import CapabilityMappingInput, CapabilityMap
from skill_quest.progression.models import ProgressionInput
from skill_quest.progression.agent import agent as progression_agent
from skill_quest.state import LearnerState


def _message_text(msg) -> str:
    content = getattr(msg, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return " ".join(p for p in parts if p).strip()
    return ""

def _latest_user_request(state: LearnerState) -> str:
    """Return the user request from state, falling back to the last human message."""
    if state.get("user_request"):
        return state["user_request"].strip()

    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            text = _message_text(msg)
            if text:
                return text

    raise ValueError("No user request found in state['user_request'] or state['messages'].")

def run_goal_agent(state: LearnerState) -> dict:
    user_request = _latest_user_request(state)

    learner_context = LearnerContext.model_validate(
        state.get("learner_context", {})
    )

    goal_input = GoalInput(
        user_request=user_request,
        learner_context=learner_context,
    )

    result = goal_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_request,
                }
            ]
        },
        context=goal_input,
    )

    skill_goal: SkillGoal = result["structured_response"]

    return {
        "user_request": user_request,
        "goal": skill_goal.model_dump(),
        "current_stage": "goal_created",
        "messages": [
            AIMessage(content=f"Goal set: {skill_goal.desired_outcome}")
        ],
    }

def run_research_agent(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])

    research_input = ResearchInput(goal=goal)

    result = research_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Research the supplied skill goal.",
                }
            ]
        },
        context=research_input,
    )

    dossier = result["structured_response"]

    source_count = len(getattr(dossier, "sources", []) or [])

    return {
        "skill_dossier": dossier.model_dump(),
        "current_stage": "research_complete",
        "messages": [
            AIMessage(
                content=f"Research complete: {source_count} sources gathered for {goal.skill}."
            )
        ],
    }

def run_capability_agent(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    dossier = SkillDossier.model_validate(state["skill_dossier"])

    capability_input = CapabilityMappingInput(
        goal = goal,
        dossier = dossier
    )

    result = capability_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Convert the supplied skill goal and research dossier into an observable capability map."
                }
            ]
        },
        context=capability_input,
    )

    capability_map = result["structured_response"]
    if not isinstance(capability_map, CapabilityMap):
        capability_map = CapabilityMap.model_validate(capability_map)

    return {
        "capability_map": capability_map.model_dump(),
        "current_stage": "capabilities_mapped",
        "error": None,
    }

def run_progression_planner(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    capabilities = CapabilityMap.model_validate(state["capability_map"]).capabilities

    progression_input = ProgressionInput(
        goal=goal,
        capabilities=capabilities
    )

    result = progression_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Progression the supplied skill goal.",
                }
            ]
        },
        context=progression_input,
    )

    progression_plan =result["structured_response"]

    return {
        "progression_plan": progression_plan.model_dump(),
        "current_stage": "progression_planned",
        "messages": [
            AIMessage(
                content=f"Progression Plan complete: {progression_plan}"
            )
        ],
        "error": None,
    }

