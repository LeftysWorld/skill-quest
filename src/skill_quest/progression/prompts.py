from langchain.agents.middleware import ModelRequest, dynamic_prompt

from skill_quest.progression.models import ProgressionInput


@dynamic_prompt
def progression_planner_prompt(request: ModelRequest) -> str:
    ctx: ProgressionInput = request.runtime.context

    return f"""
You are the Progression Planner.

Create possible routes through the learner's skill goal.

Goal:
{ctx.goal.model_dump_json(indent=2)}

Capabilities:
{ctx.model_dump_json(indent=2)}

Produce a ProgressionPlan with exactly 2 or 3 tracks.

Each track must include:
- id
- name
- identity_statement
- intended_outcome
- entry_capability_ids
- milestone_capability_groups
- optional branch_after_tier
- exit_capability_ids
- rationale

Rules:
- Use only the supplied capability IDs.
- Preserve prerequisite relationships.
- Group related capabilities into milestone-sized clusters.
- Branch by learner direction, not arbitrary difficulty.
- Keep the plan realistic for the learner's available time.
- Set recommended_track_id to one of the generated track IDs.
- Do not generate quests.
- Do not generate detailed practice sessions.
- Return only the structured ProgressionPlan object.
""".strip()
