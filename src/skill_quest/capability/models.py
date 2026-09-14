from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvidenceType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    PHOTO = "photo"
    NOTE = "note"
    WITNESS = "witness"
    READING = "reading"
    GPS = "gps"


class CapabilityCategory(StrEnum):
    KNOWLEDGE = "knowledge"
    TECHNIQUE = "technique"
    TIMING = "timing"
    PERCEPTION = "perception"
    JUDGMENT = "judgment"
    CREATIVITY = "creativity"
    COMMUNICATION = "communication"
    TRANSFER = "transfer"
    SAFETY = "safety"


CATEGORY_ALIASES = {
    "knowledge": CapabilityCategory.KNOWLEDGE,
    "technique": CapabilityCategory.TECHNIQUE,
    "timing": CapabilityCategory.TIMING,
    "perception": CapabilityCategory.PERCEPTION,
    "judgment": CapabilityCategory.JUDGMENT,
    "creativity": CapabilityCategory.CREATIVITY,
    "communication": CapabilityCategory.COMMUNICATION,
    "transfer": CapabilityCategory.TRANSFER,
    "safety": CapabilityCategory.SAFETY,

    # Normalization aliases
    "technology": CapabilityCategory.KNOWLEDGE,
    "technical": CapabilityCategory.TECHNIQUE,
    "planning": CapabilityCategory.JUDGMENT,
    "decision-making": CapabilityCategory.JUDGMENT,
    "decision_making": CapabilityCategory.JUDGMENT,
    "execution": CapabilityCategory.TECHNIQUE,
    "application": CapabilityCategory.TRANSFER,
}


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u200b", "")
    value = value.replace("\ufeff", "")
    value = value.replace("\u2060", "")
    return value.strip()


def normalize_category(value: str) -> CapabilityCategory:
    cleaned = clean_text(value).lower()
    cleaned = re.sub(r"\s+", " ", cleaned)

    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0].strip()

    if cleaned not in CATEGORY_ALIASES:
        raise ValueError(f"Unsupported capability category: {value!r}")

    return CATEGORY_ALIASES[cleaned]


class Capability(BaseModel):
    id: str
    name: str
    description: str

    categories: list[CapabilityCategory] = Field(
        min_length=1,
        description=(
            "One or more categories. Use separate enum values, "
            "not combined strings."
        ),
    )

    observable_behaviors: list[str] = Field(
        default_factory=list,
        description="Concrete behaviors another person could observe.",
    )

    prerequisite_ids: list[str] = Field(default_factory=list)
    evidence_types: list[EvidenceType] = Field(default_factory=list)

    tier_hint: int = Field(default=0, ge=0, le=5)
    estimated_days_at_30_min: int | None = Field(
        default=None,
        ge=0,
    )

    common_failure_modes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator("id", "name", "description", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return clean_text(value)
        return value

    @field_validator("categories", mode="before")
    @classmethod
    def normalize_categories(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            raise ValueError("categories must be a list or string")

        normalized: list[CapabilityCategory] = []

        for item in value:
            if isinstance(item, CapabilityCategory):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append(normalize_category(item))
            else:
                raise ValueError(
                    f"Invalid category value: {item!r}"
                )

        # Remove duplicates while preserving order.
        return list(dict.fromkeys(normalized))

    @field_validator("observable_behaviors", mode="before")
    @classmethod
    def normalize_observable_behaviors(
        cls,
        value: Any,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            return [clean_text(value)]

        if isinstance(value, list):
            return [
                clean_text(item)
                for item in value
                if isinstance(item, str) and clean_text(item)
            ]

        return []


class CapabilityMap(BaseModel):
    skill: str
    capabilities: list[Capability]
    assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class CapabilityMappingInput(BaseModel):
    goal: Any
    dossier: Any
