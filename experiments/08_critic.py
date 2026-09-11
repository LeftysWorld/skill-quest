from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

from experiments.models import (
    SkillGoal,
    SkillDossier,
    CapabilityMap,
    ProgressionPlan,
    Track,
    MilestoneSet,
    Ladder,
    QuestSet,
    QuestType,
    Critique,
)
from experiments.helpers import load_json

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest


# ---------- Load artifacts ----------

goal_json = load_json(SkillGoal, "goal.json")
skill_dossier_json = load_json(SkillDossier, "skill_dossier.json")
capability_map_json = load_json(CapabilityMap, "capability_map.json")
progression_plan_json = load_json(ProgressionPlan, "progression_plan.json")
milestone_set_json = load_json(MilestoneSet, "milestone_set.json")
ladder_json = load_json(Ladder, "ladder.json")
quest_set_json = load_json(QuestSet, "quest_set.json")


# ---------- Input schema ----------

class CriticInput(BaseModel):
    goal: SkillGoal = Field(default_factory=lambda: goal_json)
    dossier: SkillDossier = Field(default_factory=lambda: skill_dossier_json)
    capability_map: CapabilityMap = Field(default_factory=lambda: capability_map_json)
    progression_plan: ProgressionPlan = Field(default_factory=lambda: progression_plan_json)
    milestones: MilestoneSet = Field(default_factory=lambda: milestone_set_json)
    ladder: Ladder = Field(default_factory=lambda: ladder_json)
    quests: QuestSet = Field(default_factory=lambda: quest_set_json)
    deterministic_findings: list[str] = Field(default_factory=list)


# ---------- Deterministic checks ----------
# (your existing check_* functions stay exactly as they are)

def check_goal(goal: SkillGoal) -> list[str]:
    errors: list[str] = []
    if not goal.skill.strip():
        errors.append("Goal skill is empty.")
    if not goal.desired_outcome.strip():
        errors.append("Goal desired_outcome is empty.")
    if not goal.target_context.strip():
        errors.append("Goal target_context is empty.")
    if not goal.success_definition:
        errors.append("Goal has no success_definition.")
    if goal.target_weeks < 1:
        errors.append("Goal target_weeks must be at least 1.")
    if goal.minutes_per_day < 1:
        errors.append("Goal minutes_per_day must be greater than 0.")
    if goal.days_per_week < 1 or goal.days_per_week > 7:
        errors.append("Goal days_per_week must be between 1 and 7.")
    return errors


def check_dossier(dossier: SkillDossier) -> list[str]:
    errors: list[str] = []
    if not dossier.skill.strip():
        errors.append("SkillDossier skill is empty.")
    if not dossier.progression_patterns:
        errors.append("SkillDossier has no progression_patterns.")
    if not dossier.capability_candidates:
        errors.append("SkillDossier has no capability_candidates.")
    if not dossier.sources:
        errors.append("SkillDossier has no sources.")

    for source in dossier.sources:
        if not source.id.strip():
            errors.append("A source has an empty id.")
        if not source.title.strip():
            errors.append(f"Source {source.id} has an empty title.")
        if not source.url.startswith("http"):
            errors.append(f"Source {source.id} does not have a valid-looking URL.")
        if not source.extracted_claims:
            errors.append(f"Source {source.id} has no extracted claims.")
    return errors


def check_capability_map(capability_map: CapabilityMap) -> list[str]:
    errors: list[str] = []
    if not capability_map.capabilities:
        errors.append("CapabilityMap contains no capabilities.")
        return errors

    capability_ids = {c.id for c in capability_map.capabilities}

    for cap in capability_map.capabilities:
        if not cap.name.strip():
            errors.append(f"Capability {cap.id} has no name.")
        if not cap.description.strip():
            errors.append(f"Capability {cap.id} has no description.")
        if not cap.observable_behaviors:
            errors.append(f"Capability {cap.id} has no observable behaviors.")
        if not cap.evidence_types:
            errors.append(f"Capability {cap.id} has no evidence types.")

        missing_prerequisites = set(cap.prerequisite_ids) - capability_ids
        if missing_prerequisites:
            errors.append(
                f"Capability {cap.id} references missing prerequisites: "
                f"{sorted(missing_prerequisites)}"
            )
        if cap.id in cap.prerequisite_ids:
            errors.append(f"Capability {cap.id} references itself as a prerequisite.")
    return errors


def check_progression_plan(plan: ProgressionPlan, capability_map: CapabilityMap) -> list[str]:
    errors: list[str] = []
    if not plan.tracks:
        errors.append("ProgressionPlan contains no tracks.")
        return errors

    track_ids = {t.id for t in plan.tracks}
    capability_ids = {c.id for c in capability_map.capabilities}

    if plan.recommended_track_id not in track_ids:
        errors.append("ProgressionPlan recommended_track_id does not reference a valid track.")

    for cid in plan.shared_foundation_capability_ids:
        if cid not in capability_ids:
            errors.append(
                "ProgressionPlan references missing shared foundation capability: "
                f"{cid}"
            )

    for track in plan.tracks:
        errors.extend(check_track(track, capability_ids))
    return errors


def check_track(track: Track, capability_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not track.name.strip():
        errors.append(f"Track {track.id} has no name.")
    if not track.identity_statement.strip():
        errors.append(f"Track {track.id} has no identity_statement.")
    if not track.intended_outcome.strip():
        errors.append(f"Track {track.id} has no intended_outcome.")

    referenced_ids = set(track.entry_capability_ids)
    referenced_ids.update(track.exit_capability_ids)
    for group in track.milestone_capability_groups:
        referenced_ids.update(group)

    missing_ids = referenced_ids - capability_ids
    if missing_ids:
        errors.append(
            f"Track {track.id} references missing capabilities: "
            f"{sorted(missing_ids)}"
        )

    if not track.milestone_capability_groups:
        errors.append(f"Track {track.id} has no milestone capability groups.")
    return errors


def check_milestones(
    milestone_set: MilestoneSet,
    progression_plan: ProgressionPlan,
    capability_map: CapabilityMap,
) -> list[str]:
    errors: list[str] = []
    if not milestone_set.milestones:
        errors.append("MilestoneSet contains no milestones.")
        return errors

    track_ids = {t.id for t in progression_plan.tracks}
    capability_ids = {c.id for c in capability_map.capabilities}
    milestone_ids: set[str] = set()

    for ms in milestone_set.milestones:
        if ms.id in milestone_ids:
            errors.append(f"Duplicate milestone id: {ms.id}")
        milestone_ids.add(ms.id)

        if ms.track_id not in track_ids:
            errors.append(f"Milestone {ms.id} references missing track: {ms.track_id}")

        missing_caps = set(ms.capability_ids) - capability_ids
        if missing_caps:
            errors.append(
                f"Milestone {ms.id} references missing capabilities: "
                f"{sorted(missing_caps)}"
            )

        if not ms.capability_statement.strip():
            errors.append(f"Milestone {ms.id} has no capability statement.")
        if not ms.demonstration_gate.strip():
            errors.append(f"Milestone {ms.id} has no demonstration gate.")
        if not ms.pass_criteria:
            errors.append(f"Milestone {ms.id} has no pass criteria.")
        if not ms.failure_routes:
            errors.append(f"Milestone {ms.id} has no failure routes.")
        if ms.target_weeks < 1:
            errors.append(f"Milestone {ms.id} has invalid target_weeks.")

    expected_track_id = milestone_set.track_id
    if expected_track_id not in track_ids:
        errors.append("MilestoneSet track_id does not reference a valid track.")

    for ms in milestone_set.milestones:
        if ms.track_id != expected_track_id:
            errors.append(
                f"Milestone {ms.id} does not belong to the MilestoneSet "
                f"track_id {expected_track_id}."
            )
    return errors


def check_ladder(
    ladder: Ladder,
    goal: SkillGoal,
    progression_plan: ProgressionPlan,
    milestone_set: MilestoneSet,
) -> list[str]:
    errors: list[str] = []

    if ladder.goal_id != goal.id:
        errors.append("Ladder goal_id does not match SkillGoal id.")

    track_ids = {t.id for t in progression_plan.tracks}
    if ladder.selected_track_id not in track_ids:
        errors.append("Ladder selected_track_id does not reference a valid track.")

    alternate_track_ids = set(ladder.alternate_track_ids)
    missing_alternate = alternate_track_ids - track_ids
    if missing_alternate:
        errors.append(
            "Ladder references missing alternate tracks: "
            f"{sorted(missing_alternate)}"
        )

    milestone_ids = {m.id for m in milestone_set.milestones}
    missing_milestones = set(ladder.milestone_ids) - milestone_ids
    if missing_milestones:
        errors.append(
            "Ladder references missing milestones: "
            f"{sorted(missing_milestones)}"
        )

    if not ladder.milestone_ids:
        errors.append("Ladder contains no milestone IDs.")
    if not ladder.north_star_capability.strip():
        errors.append("Ladder north_star_capability is empty.")
    if ladder.target_weeks < goal.target_weeks:
        errors.append("Ladder target_weeks is shorter than the goal target_weeks.")
    if ladder.minutes_per_day != goal.minutes_per_day:
        errors.append("Ladder minutes_per_day does not match the goal.")
    return errors


def check_quests(quest_set: QuestSet, milestone_set: MilestoneSet) -> list[str]:
    errors: list[str] = []
    if not quest_set.quests:
        errors.append("QuestSet contains no quests.")
        return errors

    milestone_ids = {m.id for m in milestone_set.milestones}
    if quest_set.milestone_id not in milestone_ids:
        errors.append("QuestSet milestone_id does not reference a valid milestone.")

    quest_ids: set[str] = set()
    for q in quest_set.quests:
        if q.id in quest_ids:
            errors.append(f"Duplicate quest id: {q.id}")
        quest_ids.add(q.id)

        if q.milestone_id != quest_set.milestone_id:
            errors.append(
                f"Quest {q.id} references milestone {q.milestone_id}, "
                f"but QuestSet is for {quest_set.milestone_id}."
            )

        if not q.title.strip():
            errors.append(f"Quest {q.id} has no title.")
        if not q.purpose.strip():
            errors.append(f"Quest {q.id} has no purpose.")
        if not q.instructions:
            errors.append(f"Quest {q.id} has no instructions.")
        if not q.success_criteria:
            errors.append(f"Quest {q.id} has no success criteria.")
        if not q.evidence_required:
            errors.append(f"Quest {q.id} has no evidence requirements.")
        if not q.failure_route.strip():
            errors.append(f"Quest {q.id} has no failure route.")
        if q.estimated_days < 1:
            errors.append(f"Quest {q.id} has invalid estimated_days.")
        if q.sessions < 1:
            errors.append(f"Quest {q.id} has invalid sessions.")
        if q.minutes_per_session < 1:
            errors.append(f"Quest {q.id} has invalid minutes_per_session.")

    demonstrations = [
        q for q in quest_set.quests if q.quest_type == QuestType.DEMONSTRATION
    ]
    if len(demonstrations) != 1:
        errors.append("QuestSet must contain exactly one demonstration quest.")

    transfer_types = {
        QuestType.WORLD,
        QuestType.SOCIAL,
        QuestType.DISCOVERY,
        QuestType.CREATION,
    }
    if not any(q.quest_type in transfer_types for q in quest_set.quests):
        errors.append("QuestSet must contain at least one transfer-oriented quest.")

    drill_count = sum(q.quest_type == QuestType.DRILL for q in quest_set.quests)
    if drill_count < 1:
        errors.append("QuestSet should contain at least one drill quest.")
    return errors


def run_deterministic_checks(critic_input: CriticInput) -> list[str]:
    findings: list[str] = []

    checks = [
        ("Goal", check_goal(critic_input.goal)),
        ("Dossier", check_dossier(critic_input.dossier)),
        ("CapabilityMap", check_capability_map(critic_input.capability_map)),
        (
            "ProgressionPlan",
            check_progression_plan(critic_input.progression_plan, critic_input.capability_map),
        ),
        (
            "Milestones",
            check_milestones(critic_input.milestones, critic_input.progression_plan, critic_input.capability_map),
        ),
        (
            "Ladder",
            check_ladder(critic_input.ladder, critic_input.goal, critic_input.progression_plan, critic_input.milestones),
        ),
        ("Quests", check_quests(critic_input.quests, critic_input.milestones)),
    ]

    for artifact_name, errors in checks:
        for error in errors:
            findings.append(f"{artifact_name}: {error}")
    return findings


# ---------- Prompt middleware ----------

@dynamic_prompt
def critic_prompt(request: ModelRequest) -> str:
    ctx: CriticInput = request.runtime.context

    # Run deterministic checks once per invocation and inject findings
    deterministic_findings = run_deterministic_checks(ctx)

    return f"""
You are the Critic for a skill-development ladder system.

Your job is to review the bundle of planning artifacts before they are accepted.

You are reviewing:
- SkillGoal
- SkillDossier
- CapabilityMap
- ProgressionPlan
- MilestoneSet
- Ladder
- QuestSet

Deterministic findings from code:
{deterministic_findings}

Review the artifacts for soft quality issues:

1. Goal quality
- Is the desired outcome concrete and real-world?
- Are success definitions observable?
- Is the time horizon plausible?

2. Research quality
- Are sources present and relevant?
- Are claims distinguished from assumptions?
- Are uncertainties acknowledged?

3. Capability quality
- Are capabilities things the learner can demonstrably do?
- Are observable behaviors specific?
- Are prerequisites coherent?
- Are capabilities more than topics or lessons?

4. Progression quality
- Do the tracks represent meaningful directions?
- Is the recommended track aligned with the goal?
- Are branch points sensible?
- Is sequencing coherent?

5. Milestone quality
- Is each milestone a named capability?
- Does each have a meaningful demonstration gate?
- Are pass criteria observable?
- Are failure routes useful?
- Does the sequence build toward the goal?

6. Quest quality
- Are quests clearly tied to the milestone?
- Are there drill and transfer-oriented quests?
- Is there exactly one demonstration quest?
- Is the demonstration actually testing the milestone?
- Are success criteria observable?
- Are pacing fields realistic?
- Is the resource link, if present, relevant?
- Are twists meaningful rather than decorative?

Critique rules:
- Treat deterministic findings as hard failures unless they are clearly false.
- Use hard_failures for structural or blocking problems.
- Use soft_failures for quality problems that require revision.
- Use warnings for non-blocking concerns.
- Provide specific rewrite instructions.
- Do not create replacement goals, milestones, or quests.
- Do not validate physical guitar performance.
- Do not provide coaching.
- Do not provide a long explanation.

Return only a Critique object.

Use:
- target_type: "ladder_package"
- target_id: {ctx.ladder.id}
- status: "approved" if there are no blocking issues,
  "revise" if changes are needed but the artifacts are usable,
  or "rejected" if the package is structurally unusable.
""".strip()


# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    middleware=[critic_prompt],
    context_schema=CriticInput,
    response_format=Critique,
)
