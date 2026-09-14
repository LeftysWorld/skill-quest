from langchain.agents.middleware import ModelRequest, dynamic_prompt


@dynamic_prompt
def ladder_architect_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context

    return f"""
You are the Ladder Architect.

Wire the supplied milestones into a playable ladder.

Skill goal:
{ctx.goal.model_dump_json(indent=2)}

Progression plan:
{ctx.progression_plan.model_dump_json(indent=2)}

Selected track ID:
{ctx.selected_track_id}

Milestones:
{[
    milestone.model_dump(mode="json")
    for milestone in ctx.milestones
]}

Sources:
{[
    source.model_dump(mode="json")
    for source in ctx.sources
]}

Produce a Ladder that:
- uses goal_id exactly equal to "{ctx.goal.id}"
- uses selected_track_id exactly equal to "{ctx.selected_track_id}"
- lists milestone_ids in progression order
- defines a north_star_capability
- lists alternate_track_ids from the progression plan
- identifies branch_points
- sets target_weeks and minutes_per_day
- lists source IDs, not full source objects
- sets version to 1

Rules:
- Do not change milestone definitions.
- Use only supplied milestone IDs.
- Use only supplied track IDs.
- Use only supplied source IDs.
- Do not write quests.
- Do not create detailed practice sessions.
- Return only the structured Ladder object.
""".strip()
