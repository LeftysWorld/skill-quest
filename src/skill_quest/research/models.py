from __future__ import annotations

from pydantic import BaseModel, Field

from skill_quest.goal.models import SkillGoal

class ResearchInput(BaseModel):
    goal: SkillGoal


class SourceRecord(BaseModel):
    id: str
    title: str
    url: str
    source_type: str
    publisher: str | None = None
    relevance: str
    extracted_claims: list[str] = Field(default_factory=list)
    retrieved_at: str | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class SkillDossier(BaseModel):
    skill: str
    scope: str
    progression_patterns: list[str]
    capability_candidates: list[str]
    prerequisite_patterns: list[str] = Field(default_factory=list)
    common_failure_modes: list[str] = Field(default_factory=list)
    safety_constraints: list[str] = Field(default_factory=list)
    authentic_contexts: list[str] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
