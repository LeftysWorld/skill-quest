from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------- Enums ----------

class EvidenceType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    PHOTO = "photo"
    NOTE = "note"
    WITNESS = "witness"
    READING = "reading"
    GPS = "gps"


class QuestType(StrEnum):
    DRILL = "drill"
    WORLD = "world"
    DISCOVERY = "discovery"
    CREATION = "creation"
    SOCIAL = "social"
    DEMONSTRATION = "demonstration"


class CapabilityCategory(StrEnum):
    KNOWLEDGE = "knowledge"
    TECHNIQUE = "technique"
    TIMING = "timing"
    PERCEPTION = "perception"
    JUDGMENT = "judgment"
    CREATIVITY = "creativity"
    COMMUNICATION = "communication"
    TRANSFER = "transfer"


class CritiqueStatus(StrEnum):
    APPROVED = "approved"
    REVISE = "revise"
    REJECTED = "rejected"


# ---------- Artifact Metadata ----------

# It is useful for every saved artifact to know which agent produced it.
class ArtifactMetadata(BaseModel):
    artifact_id: str
    artifact_type: str
    produced_by: str
    model_name: str | None = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1


# ---------- Models ----------

class SkillGoal(BaseModel):
    id: str
    skill: str
    desired_outcome: str
    target_context: str
    success_definition: list[str]
    target_weeks: int = Field(ge=1)
    minutes_per_day: int = Field(gt=0)
    days_per_week: int = Field(ge=1, le=7)
    motivation: str | None = None
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


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
    design_notes: list[str] = Field(default_factory=list)


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


class LadderPackage(BaseModel):
    goal: SkillGoal
    dossier: SkillDossier
    capability_map: CapabilityMap
    progression_plan: ProgressionPlan
    milestone_set: MilestoneSet
    ladder: Ladder
    quest_set: QuestSet

class Verdict(BaseModel):
    quest_id: str
    evidence_status: Literal[
        "verified",
        "incomplete",
        "pending_review",
        "rejected",
    ]
    observed_measurements: dict[str, Any] = Field(default_factory=dict)
    observed_strengths: list[str] = Field(default_factory=list)
    observed_weaknesses: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""


class Assessment(BaseModel):
    milestone_id: str
    quest_id: str
    status: Literal[
        "passed",
        "partial",
        "failed",
        "insufficient_evidence",
    ]
    score: float = Field(ge=0.0, le=1.0)
    criterion_results: dict[str, bool | str | float] = Field(
        default_factory=dict
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    limiting_gap: str | None = None
    recommended_target: str | None = None


class ProgressionDecision(BaseModel):
    action: Literal[
        "advance",
        "retry",
        "remediate",
        "branch",
        "pause",
        "rest",
    ]
    current_milestone_id: str
    target_milestone_id: str | None = None
    target_capability_ids: list[str] = Field(default_factory=list)
    rationale: str
    next_quest_requirements: list[str] = Field(default_factory=list)
    player_model_updates: dict[str, Any] = Field(default_factory=dict)


class Critique(BaseModel):
    target_type: str
    target_id: str
    status: CritiqueStatus
    hard_failures: list[str] = Field(default_factory=list)
    soft_failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rewrite_instructions: list[str] = Field(default_factory=list)
