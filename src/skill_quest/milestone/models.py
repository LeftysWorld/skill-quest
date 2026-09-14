from __future__ import annotations

from pydantic import BaseModel, Field

from skill_quest.goal.models import SkillGoal
from skill_quest.progression.models import ProgressionPlan, ProgressionCapability


class MilestoneDesignInput(BaseModel):
    goal: SkillGoal
    capabilities: list[ProgressionCapability]
    progression_plan: ProgressionPlan
    selected_track_id: str


class Milestone(BaseModel):
    id: str
    track_id: str
    tier: int = Field(ge=0)
    title: str
    capability_ids: list[str]
    capability_statement: str
    why_it_matters: str
    target_weeks: int = Field(ge=1)
    demonstration_gate: str
    pass_criteria: list[str]
    failure_routes: list[str]
    unlocks: list[str] = Field(default_factory=list)


# Milestone wrapper
class MilestoneSet(BaseModel):
    track_id: str
    milestones: list[Milestone]
    design_rationale: list[str] = Field(default_factory=list)
