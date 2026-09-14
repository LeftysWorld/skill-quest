from pydantic import BaseModel, Field
from enum import StrEnum

from skill_quest.capability.models import EvidenceType
from skill_quest.goal.models import SkillGoal
from skill_quest.milestone.models import Milestone
from skill_quest.progression.models import ProgressionCapability
from skill_quest.research.models import SourceRecord


class QuestType(StrEnum):
    DRILL = "drill"
    WORLD = "world"
    DISCOVERY = "discovery"
    CREATION = "creation"
    SOCIAL = "social"
    DEMONSTRATION = "demonstration"


class QuestDesignInput(BaseModel):
    goal: SkillGoal
    milestone: Milestone
    capabilities: list[ProgressionCapability]
    sources: list[SourceRecord]


class EvidenceSpec(BaseModel):
    type: EvidenceType
    purpose: str
    required: bool = True
    duration_seconds: int | None = Field(default=None, ge=1)
    must_show: list[str] = Field(default_factory=list)


class Quest(BaseModel):
    id: str
    milestone_id: str
    quest_type: QuestType
    title: str
    purpose: str
    instructions: list[str]
    estimated_days: int = Field(ge=1)
    sessions: int = Field(ge=1)
    minutes_per_session: int = Field(gt=0)
    success_criteria: list[str]
    evidence_required: list[EvidenceSpec]
    resource_url: str | None = None
    resource_reason: str | None = None
    twist: str | None = None
    failure_route: str
    optional: bool = False


# Quest Wrapper
class QuestSet(BaseModel):
    milestone_id: str
    quests: list[Quest]
    recommended_quest_id: str | None = None
    design_notes: list[str] = Field(default_factory=list)
