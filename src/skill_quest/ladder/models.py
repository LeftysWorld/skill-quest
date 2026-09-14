from __future__ import annotations

from pydantic import BaseModel, Field

from skill_quest.goal.models import SkillGoal
from skill_quest.milestone.models import Milestone
from skill_quest.progression.models import ProgressionPlan
from skill_quest.research.models import SourceRecord


class LadderInput(BaseModel):
    goal: SkillGoal
    progression_plan: ProgressionPlan
    milestones: list[Milestone]
    sources: list[SourceRecord]
    selected_track_id: str


class Ladder(BaseModel):
    id: str
    goal_id: str
    title: str
    skill: str
    north_star_capability: str
    selected_track_id: str
    alternate_track_ids: list[str] = Field(default_factory=list)
    milestone_ids: list[str]
    branch_points: list[str] = Field(default_factory=list)
    target_weeks: int = Field(ge=1)
    minutes_per_day: int = Field(gt=0)
    sources: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    version: int = 1
