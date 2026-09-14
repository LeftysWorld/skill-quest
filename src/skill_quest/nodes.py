from __future__ import annotations

from langchain_core.messages import AIMessage

from skill_quest.goal.agent import agent as goal_agent
from skill_quest.goal.models import GoalInput, LearnerContext, SkillGoal
from skill_quest.research.agent import agent as research_agent
from skill_quest.research.models import ResearchInput, SkillDossier, SourceRecord
from skill_quest.capability.agent import agent as capability_agent
from skill_quest.capability.models import CapabilityMappingInput, CapabilityMap
from skill_quest.progression.models import ProgressionCapability, ProgressionInput, ProgressionPlan
from skill_quest.progression.agent import agent as progression_agent
from skill_quest.milestone.agent import agent as milestone_agent
from skill_quest.milestone.models import MilestoneDesignInput, MilestoneSet
from skill_quest.ladder.agent import agent as ladder_agent
from skill_quest.ladder.models import LadderInput, Ladder
from skill_quest.quest.agent import agent as quest_agent
from skill_quest.quest.models import QuestDesignInput, QuestSet, QuestType


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
    _defaults = [
            ("Demonstrate the target skill in the stated context using the available equipment."),
            ("Complete a continuous performance or practical task without stopping."),
            ("Provide observable evidence that another person could review."),
        ]
    success_definition = [item.strip() for item in skill_goal.success_definition
        if isinstance(item, str) and item.strip()
    ]

    if not success_definition:
        success_definition = _defaults

    if len(success_definition) < 3:
        defaults = _defaults

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

def run_ladder_planner(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    progression_plan = ProgressionPlan.model_validate(state["progression_plan"])
    milestone_set = MilestoneSet.model_validate(state["milestone_design"])
    dossier = SkillDossier.model_validate(state["skill_dossier"])
    selected_track_id = state.get("selected_track_id")

    if not selected_track_id:
        raise ValueError(
            "No selected_track_id found in learner state."
        )

    if milestone_set.track_id != selected_track_id:
        raise ValueError(
            "MilestoneSet.track_id does not match selected_track_id."
        )

    source_records = [SourceRecord.model_validate(source) for source in dossier.sources]

    ladder_input = LadderInput(
        goal=goal,
        progression_plan=progression_plan,
        milestones=milestone_set.milestones,
        sources=source_records,
        selected_track_id=selected_track_id,
    )

    result = ladder_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Assemble the approved milestones into "
                        "a playable ladder for the selected track."
                    ),
                }
            ]
        },
        context=ladder_input,
    )

    ladder = result["structured_response"]

    if not isinstance(ladder, Ladder):
        ladder = Ladder.model_validate(ladder)

    if ladder.goal_id != goal.id:
        raise ValueError(
            "Ladder.goal_id does not match the current goal ID."
        )

    if ladder.selected_track_id != selected_track_id:
        raise ValueError(
            "Ladder.selected_track_id does not match the selected track."
        )

    approved_milestone_ids = {milestone.id for milestone in milestone_set.milestones}
    unknown_milestone_ids = (set(ladder.milestone_ids) - approved_milestone_ids)

    if unknown_milestone_ids:
        raise ValueError(
            "Ladder references unknown milestone IDs: "
            f"{sorted(unknown_milestone_ids)}"
        )

    if not ladder.milestone_ids:
        raise ValueError(
            "Ladder contains no milestone IDs."
        )

    approved_track_ids = {track.id for track in progression_plan.tracks}

    if ladder.selected_track_id not in approved_track_ids:
        raise ValueError(
            "Ladder.selected_track_id is not present in the ProgressionPlan."
        )

    unknown_alternate_track_ids = (set(ladder.alternate_track_ids) - approved_track_ids)

    if unknown_alternate_track_ids:
        raise ValueError(
            "Ladder references unknown alternate track IDs: "
            f"{sorted(unknown_alternate_track_ids)}"
        )

    approved_source_ids = {source.id for source in source_records}
    unknown_source_ids = (set(ladder.sources) - approved_source_ids)

    if unknown_source_ids:
        ladder.sources = [source_id for source_id in ladder.sources if source_id in approved_source_ids]

        ladder.assumptions.append(
            "The Ladder Architect generated unsupported "
            "source references. They were removed: "
            f"{sorted(unknown_source_ids)}"
        )

    return {
        "ladder_architect": ladder.model_dump(mode="json"),
        "current_stage": "ladder_created",
        "messages": [
            AIMessage(
                content=(
                    "Ladder architecture complete: "
                    f"{ladder.title}"
                )
            )
        ],
        "error": None,
    }

def run_quest_planner(state: LearnerState) -> dict:
    goal = SkillGoal.model_validate(state["goal"])
    capability_map = CapabilityMap.model_validate(state["capability_map"])
    milestone_set = MilestoneSet.model_validate(state["milestone_design"])
    dossier = SkillDossier.model_validate(state["skill_dossier"])
    selected_track_id = state.get("selected_track_id")

    if not selected_track_id:
        raise ValueError(
            "No selected_track_id found in learner state."
        )

    selected_milestone = min(milestone_set.milestones, key=lambda milestone: milestone.tier)

    progression_capabilities = [
        ProgressionCapability(
            id=capability.id,
            name=capability.name,
            categories=capability.categories,
            observable_behaviors=(capability.observable_behaviors),
            prerequisite_ids=(capability.prerequisite_ids),
            tier_hint=capability.tier_hint,
        )
        for capability in capability_map.capabilities
    ]

    source_records = [SourceRecord.model_validate(source) for source in dossier.sources]

    quest_input = QuestDesignInput(
        goal=goal,
        milestone=selected_milestone,
        capabilities=progression_capabilities,
        sources=source_records,
    )

    result = quest_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Create five quests for the selected milestone."
                    ),
                }
            ]
        },
        context=quest_input,
    )

    quest_set = result["structured_response"]
    if not isinstance(quest_set, QuestSet):
        quest_set = QuestSet.model_validate(quest_set)

    if quest_set.milestone_id != selected_milestone.id:
        raise ValueError(
            "QuestSet.milestone_id does not match selected milestone."
        )

    if len(quest_set.quests) != 5:
        raise ValueError(
            "Quest Designer must return exactly five quests."
        )

    return {
        "quest_set": quest_set.model_dump(mode="json"),
        "current_stage": "quests_created",
        "messages": [
            AIMessage(
                content=(
                    f"Quest set created: "
                    f"{len(quest_set.quests)} quests."
                )
            )
        ],
        "error": None,
    }

def select_recommended_quest(state: LearnerState) -> dict:
    quest_set = QuestSet.model_validate(state["quest_set"])

    if not quest_set.quests:
        raise ValueError(
            "QuestSet contains no quests."
        )

    quest_ids = {quest.id for quest in quest_set.quests}

    selected_quest_id = (quest_set.recommended_quest_id)

    if selected_quest_id not in quest_ids:
        drill_quests = [quest for quest in quest_set.quests if quest.quest_type == QuestType.DRILL]
        selected_quest = (drill_quests[0] if drill_quests else quest_set.quests[0])
        selected_quest_id = selected_quest.id
    else:
        selected_quest = next(quest for quest in quest_set.quests if quest.id == selected_quest_id)

    criteria = "\n".join(f"- {criterion}" for criterion in selected_quest.success_criteria)
    instructions = "\n".join(f"{index}. {instruction}" for index, instruction in enumerate( selected_quest.instructions, start=1))

    return {
        "selected_quest_id": selected_quest_id,
        "current_stage": "quest_selected",
        "messages": [
            AIMessage(
                content=(
                    f"Recommended quest: "
                    f"{selected_quest.title}\n\n"
                    f"Type: "
                    f"{selected_quest.quest_type.value}\n\n"
                    f"Purpose: {selected_quest.purpose}\n\n"
                    f"Instructions:\n{instructions}\n\n"
                    f"Success criteria:\n{criteria}"
                )
            )
        ],
        "error": None,
    }
