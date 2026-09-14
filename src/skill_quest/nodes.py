from __future__ import annotations

from langchain_core.messages import AIMessage

from skill_quest.goal.agent import agent as goal_agent
from skill_quest.goal.models import GoalInput, LearnerContext, SkillGoal
from skill_quest.research.agent import agent as research_agent
from skill_quest.research.models import ResearchInput, SkillDossier
from skill_quest.capability.agent import agent as capability_agent
from skill_quest.capability.models import CapabilityMappingInput, CapabilityMap
from skill_quest.progression.models import ProgressionCapability, ProgressionInput, ProgressionPlan
from skill_quest.progression.agent import agent as progression_agent
from skill_quest.milestone.agent import agent as milestone_agent
from skill_quest.milestone.models import MilestoneDesignInput, MilestoneSet

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

def ensure_skill_goal_quality(skill_goal: SkillGoal, learner_context: LearnerContext) -> SkillGoal:
    success_definition = [item.strip() for item in skill_goal.success_definition
        if isinstance(item, str) and item.strip()
    ]

    if not success_definition:
        success_definition = [
            (
                "Demonstrate the target skill in the stated context "
                "using the available equipment."
            ),
            (
                "Complete a continuous performance or practical task "
                "without stopping."
            ),
            (
                "Provide observable evidence that another person "
                "could review."
            ),
        ]

    if len(success_definition) < 3:
        defaults = [
            (
                "Demonstrate the target skill in the stated context "
                "using the available equipment."
            ),
            (
                "Complete a continuous performance or practical task "
                "without stopping."
            ),
            (
                "Provide observable evidence that another person "
                "could review."
            ),
        ]

        for item in defaults:
            if item not in success_definition:
                success_definition.append(item)

            if len(success_definition) >= 3:
                break

    skill_goal.success_definition = success_definition

    return skill_goal

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

    skill_goal = result["structured_response"]

    if not isinstance(skill_goal, SkillGoal):
        skill_goal = SkillGoal.model_validate(skill_goal)

    skill_goal = ensure_skill_goal_quality(
        skill_goal,
        learner_context,
    )

    return {
        "user_request": user_request,
        "goal": skill_goal.model_dump(mode="json"),
        "current_stage": "goal_created",
        "messages": [
            AIMessage(
                content=(
                    f"Goal set: "
                    f"{skill_goal.desired_outcome}"
                )
            )
        ],
        "error": None,
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
    goal = SkillGoal.model_validate(
        state["goal"]
    )
    dossier = SkillDossier.model_validate(
        state["skill_dossier"]
    )

    capability_input = CapabilityMappingInput(
        goal=goal,
        dossier=dossier,
    )

    result = capability_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Create the observable capability map from "
                        "the supplied goal and research dossier."
                    ),
                }
            ]
        },
        context=capability_input,
    )

    capability_map = result["structured_response"]

    if not isinstance(capability_map, CapabilityMap):
        capability_map = CapabilityMap.model_validate(
            capability_map
        )

    invalid_observable = [
        capability.id
        for capability in capability_map.capabilities
        if not capability.observable_behaviors
    ]

    if invalid_observable:
        raise ValueError(
            "Capabilities missing observable behaviors: "
            f"{invalid_observable}"
        )

    return {
        "capability_map": capability_map.model_dump(
            mode="json"
        ),
        "current_stage": "capabilities_mapped",
        "messages": [
            AIMessage(
                content=(
                    "Capability mapping complete. "
                    f"{len(capability_map.capabilities)} "
                    "capabilities identified."
                )
            )
        ],
        "error": None,
    }

def run_progression_planner(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    capability_map = CapabilityMap.model_validate(state["capability_map"])

    progression_capabilities = [
        ProgressionCapability(
            id=capability.id,
            name=capability.name,
            categories=capability.categories,
            observable_behaviors=capability.observable_behaviors,
            prerequisite_ids=capability.prerequisite_ids,
            tier_hint=capability.tier_hint,
        )
        for capability in capability_map.capabilities
    ]

    progression_input = ProgressionInput(
        goal=goal,
        capabilities=progression_capabilities,
    )

    result = progression_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Create progression tracks for the supplied "
                        "skill goal and capability map."
                    ),
                }
            ]
        },
        context=progression_input,
    )

    progression_plan = result["structured_response"]

    if not isinstance(progression_plan, ProgressionPlan):
        progression_plan = ProgressionPlan.model_validate(
            progression_plan
        )

    if not progression_plan.tracks:
        raise ValueError(
            "Progression Planner returned no tracks."
        )

    track_ids = {track.id for track in progression_plan.tracks}

    if (progression_plan.recommended_track_id not in track_ids):
        raise ValueError(
            "Progression Planner returned an invalid "
            "recommended_track_id: "
            f"{progression_plan.recommended_track_id!r}"
        )

    return {
        "progression_plan": progression_plan.model_dump(
            mode="json"
        ),
        "current_stage": "progression_planned",
        "messages": [
            AIMessage(
                content=(
                    "Progression plan complete: "
                    f"{len(progression_plan.tracks)} "
                    "tracks created."
                )
            )
        ],
        "error": None,
    }

def select_recommended_track(state: LearnerState) -> dict:
    progression_plan = ProgressionPlan.model_validate(
        state["progression_plan"]
    )

    recommended_track_id = (
        progression_plan.recommended_track_id
    )

    selected_track = next(
        (
            track
            for track in progression_plan.tracks
            if track.id == recommended_track_id
        ),
        None,
    )

    if selected_track is None:
        raise ValueError(
            "ProgressionPlan.recommended_track_id does not "
            "match any track in the plan."
        )

    return {
        "selected_track_id": selected_track.id,
        "current_stage": "track_selected",
        "messages": [
            AIMessage(
                content=(
                    f"Recommended track selected: "
                    f"{selected_track.name}. "
                    f"Outcome: "
                    f"{selected_track.intended_outcome}"
                )
            )
        ],
        "error": None,
    }

def run_milestone_planner(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    capability_map = CapabilityMap.model_validate(state["capability_map"])
    progression_plan = ProgressionPlan.model_validate(state["progression_plan"])
    selected_track_id = state.get("selected_track_id")

    if not selected_track_id:
        raise ValueError(
            "No selected_track_id found in learner state."
        )

    progression_capabilities = [
        ProgressionCapability(
            id=capability.id,
            name=capability.name,
            categories=capability.categories,
            observable_behaviors=capability.observable_behaviors,
            prerequisite_ids=capability.prerequisite_ids,
            tier_hint=capability.tier_hint,
        )
        for capability in capability_map.capabilities
    ]

    milestone_input = MilestoneDesignInput(
        goal=goal,
        capabilities=progression_capabilities,
        progression_plan=progression_plan,
        selected_track_id=selected_track_id
    )

    result = milestone_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Create milestone planner for the selected progression track."
                }
            ]
        },
        context=milestone_input,
    )

    milestone_set = result["structured_response"]

    if not isinstance(milestone_set, MilestoneSet):
        milestone_set = MilestoneSet.model_validate(
            milestone_set
        )

    if milestone_set.track_id != selected_track_id:
        raise ValueError(
            "MilestoneSet.track_id does not match "
            "selected_track_id."
        )

    if not milestone_set.milestones:
        raise ValueError(
            "Milestone Designer returned no milestones."
        )

    invalid_track_ids = [milestone.id for milestone in milestone_set.milestones
                         if milestone.track_id != selected_track_id]

    if invalid_track_ids:
        raise ValueError(
            "Milestones with incorrect track_id: "
            f"{invalid_track_ids}"
        )

    return {
        "milestone_design": milestone_set.model_dump(
            mode="json"
        ),
        "current_stage": "milestone_planned",
        "messages": [
            AIMessage(
                content=(
                    "Milestone design complete: "
                    f"{len(milestone_set.milestones)} "
                    "milestones created."
                )
            )
        ],
        "error": None,
    }

def finalize_planning(state: LearnerState) -> dict:
    milestone_design = MilestoneSet.model_validate(
        state["milestone_design"]
    )

    return {
        "current_stage": "planning_complete",
        "messages": [
            AIMessage(
                content=(
                    "Planning complete. "
                    f"Created {len(milestone_design.milestones)} "
                    "milestones for your recommended track."
                )
            )
        ],
        "error": None,
    }
