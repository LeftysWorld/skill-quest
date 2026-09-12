from skill_quest.goal.models import SkillGoal
from skill_quest.research.models import SkillDossier
from pydantic import BaseModel, Field
from enum import StrEnum

class CapabilityCategory(StrEnum):
    KNOWLEDGE = "knowledge"
    TECHNIQUE = "technique"
    TIMING = "timing"
    PERCEPTION = "perception"
    JUDGMENT = "judgment"
    CREATIVITY = "creativity"
    COMMUNICATION = "communication"
    TRANSFER = "transfer"


class EvidenceType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    PHOTO = "photo"
    NOTE = "note"
    WITNESS = "witness"
    READING = "reading"
    GPS = "gps"


class CapabilityMappingInput(BaseModel):
    goal: SkillGoal
    dossier: SkillDossier


class Capability(BaseModel):
    id: str
    name: str
    description: str
    category: CapabilityCategory
    observable_behaviors: list[str]
    prerequisite_ids: list[str] = Field(default_factory=list)
    evidence_types: list[EvidenceType]
    tier_hint: int = Field(ge=0)
    estimated_days_at_30_min: int | None = Field(default=None, ge=1)
    common_failure_modes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


# Capability Wrapper
class CapabilityMap(BaseModel):
    skill: str
    capabilities: list[Capability]
    assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
