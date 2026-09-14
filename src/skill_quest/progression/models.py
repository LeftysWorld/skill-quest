from pydantic import BaseModel, Field

from skill_quest.capability.models import CapabilityCategory, EvidenceType
from skill_quest.goal.models import SkillGoal


class ProgressionCapability(BaseModel):
    id: str
    name: str
    categories: list[CapabilityCategory]
    observable_behaviors: list[str] = Field(
        default_factory=list
    )
    prerequisite_ids: list[str] = Field(
        default_factory=list
    )
    tier_hint: int = Field(default=0, ge=0, le=5)


class ProgressionInput(BaseModel):
    goal: SkillGoal
    capabilities: list[ProgressionCapability]


class Track(BaseModel):
    id: str
    name: str
    identity_statement: str
    intended_outcome: str
    entry_capability_ids: list[str] = Field(
        default_factory=list
    )
    milestone_capability_groups: list[list[str]]
    branch_after_tier: int | None = None
    exit_capability_ids: list[str] = Field(
        default_factory=list
    )
    rationale: str


class ProgressionPlan(BaseModel):
    skill: str
    recommended_track_id: str
    tracks: list[Track]
    shared_foundation_capability_ids: list[str] = Field(default_factory=list)
    branch_points: list[str] = Field(default_factory=list)
    sequencing_rationale: list[str] = Field(default_factory=list)
    pacing_rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
