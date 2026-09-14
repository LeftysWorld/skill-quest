from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class LearnerContext(BaseModel):
    learner_name: str = "Elliot"

    current_skill_level: Literal[
        "unknown",
        "beginner",
        "intermediate",
        "advanced",
    ] = "beginner"

    available_minutes_per_day: int = Field(default=30, gt=0)
    available_days_per_week: int = Field(default=5, ge=1, le=7)
    default_target_weeks: int = Field(default=8, ge=1)

    equipment: list[str] = Field(
        default_factory=lambda: [
            "electric guitar",
            "amplifier",
            "cable",
            "tuner",
            "picks",
            "strap",
            "loop pedal",
        ]
    )

    location: str | None = None
    prior_experience: str | None = None
    physical_constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)


class GoalInput(BaseModel):
    user_request: str
    learner_context: LearnerContext


class SkillGoal(BaseModel):
    id: str
    skill: str
    desired_outcome: str
    target_context: str
    success_definition: list[str] = Field(
        default_factory=list,
        description=(
            "Observable conditions another person could verify."
        ),
    )
    target_weeks: int = Field(ge=1)
    minutes_per_day: int = Field(gt=0)
    days_per_week: int = Field(ge=1, le=7)
    motivation: str | None = None
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
