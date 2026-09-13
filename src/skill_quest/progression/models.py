from pydantic import BaseModel, Field

from skill_quest.capability.models import Capability
from skill_quest.goal.models import SkillGoal


class ProgressionInput(BaseModel):
    goal: SkillGoal
    capabilities: list[Capability]


class Track(BaseModel):
    id: str
    name: str
    identity_statement: str
    intended_outcome: str
    entry_capability_ids: list[str] = Field(default_factory=list)
    milestone_capability_groups: list[list[str]]
    branch_after_tier: int | None = None
    exit_capability_ids: list[str] = Field(default_factory=list)
    rationale: str


class ProgressionPlan(BaseModel):
    skill: str
    recommended_track_id: str
    tracks: list[Track]
    shared_foundation_capability_ids: list[str] = Field(
        default_factory=list
    )
    branch_points: list[str] = Field(default_factory=list)
    sequencing_rationale: list[str] = Field(default_factory=list)
    pacing_rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
