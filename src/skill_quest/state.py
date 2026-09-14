from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class LearnerState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]

    user_request: str
    learner_context: dict[str, Any]

    goal: dict[str, Any]
    skill_dossier: dict[str, Any]
    capability_map: dict[str, Any]
    progression_plan: dict[str, Any]
    milestone_design: dict[str, Any]
    ladder_architect: dict[str, Any]
    quest_set: dict[str, Any]

    selected_track_id: str | None
    selected_quest_id: str | None

    current_stage: str
    error: str | None
