from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env" # Load .env from the root
load_dotenv(dotenv_path=env_path)

from experiments.models import SkillGoal

from typing import Literal
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

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


# ---------- Input schema ----------

class GoalInput(BaseModel):
    user_request: str = ""
    learner_context: LearnerContext = Field(default_factory=LearnerContext)


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def goal_prompt(request: ModelRequest) -> str:
    ctx: GoalInput = request.runtime.context
    learner = ctx.learner_context

    user_request = ctx.user_request.strip()

    if not user_request:
        messages = request.state.get("messages", [])

        for message in reversed(messages):
            content = getattr(message, "content", None)

            if isinstance(content, str) and content.strip():
                user_request = content.strip()
                break

    if not user_request:
        user_request = (
            "No goal was provided. Ask the learner to describe the skill "
            "they want to develop and the outcome they want to achieve."
        )

    return f"""
You are the Goal Agent.

Convert the learner's raw ambition into one concrete, observable SkillGoal.

User request:
{user_request}

Learner context:
- Name: {learner.learner_name}
- Current skill level: {learner.current_skill_level}
- Available minutes per day: {learner.available_minutes_per_day}
- Available days per week: {learner.available_days_per_week}
- Default target horizon: {learner.default_target_weeks} weeks
- Equipment: {learner.equipment}
- Location: {learner.location}
- Prior experience: {learner.prior_experience}
- Physical constraints: {learner.physical_constraints}
- Preferences: {learner.preferences}

Produce a SkillGoal with:
- skill
- desired_outcome
- target_context
- observable success_definition
- realistic target_weeks
- minutes_per_day
- days_per_week
- constraints
- assumptions

Rules:
- Use the user's request as the primary source of the desired outcome.
- Use learner context to fill in schedule, level, equipment, and constraints.
- If the user gives a timeframe, use it.
- If the user does not give a timeframe, use the default target horizon
  and record that choice in assumptions.
- Correct obvious spelling errors when the intended meaning is clear.
- Make success criteria observable by another person.
- Do not perform research.
- Do not design milestones.
- Do not generate quests.
- Do not create a practice plan.
- Do not provide coaching or a long explanation.

Return only the structured SkillGoal object.
""".strip()

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[goal_prompt],
    context_schema=GoalInput,
    response_format=SkillGoal,
)
