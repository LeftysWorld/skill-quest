# Skill Quest

Skill Quest is a stateful, AI-powered skill-development system that turns a learner's ambition into a structured journey of capabilities, progression tracks, milestones, and quests.

The long-term product goal is to move beyond curriculum generation. Skill Quest should act as a game master for real skill development: it creates a path, gives the learner meaningful missions, tracks state, and eventually adapts the next challenge based on demonstrated evidence.

## Current status

The current implementation is a Phase 1 planning engine built with LangGraph and LangChain.

It currently runs this workflow:

```text
User request
  -> Goal Agent
  -> Research Agent
  -> Capability Mapper
  -> Progression Planner
  -> Select Recommended Track
  -> Milestone Designer
  -> Finalize Planning
  -> Ladder Architect
  -> Quest Designer
  -> Select Recommended Quest
  -> Final state
```

The current system produces:

- A normalized `SkillGoal`.
- A source-backed `SkillDossier`.
- An observable `CapabilityMap`.
- Multiple progression `Track` options.
- A selected recommended track.
- A set of capability-based `Milestone` objects.
- A structured `Ladder`.
- A set of quests for the initial milestone.
- A selected recommended quest.

The system does not yet validate guitar performance or automatically assess submitted evidence.

## Product vision

Skill Quest is intended to become a full skill-development application based on two connected loops.

### Build loop

```text
Ambition
  -> research
  -> capabilities
  -> tracks
  -> milestones
  -> ladder
  -> quests
```

### Play loop

```text
Quest
  -> learner action
  -> evidence
  -> verification
  -> assessment
  -> updated capability state
  -> next quest
```

The build loop creates the learning world. The play loop makes it adaptive and alive.

## Core concepts

### Goal

A concrete statement of what the learner wants to be able to do in a real context.

### Capability

An observable ability, rather than a topic or lesson. For example:

> Maintain a steady pulse while changing between four open chords for three minutes at a target tempo.

### Track

A direction or identity the learner can pursue, such as:

- Song and Stage.
- Melody Over Chords.
- Riff and Tone.
- Loop and Layer.
- Blues and Improvisation.

### Milestone

The load-bearing object in the system. A milestone is a named capability with a demonstration gate, pass criteria, failure routes, and unlocks.

A milestone is supported by several quests and closes only when its demonstration is judged.

### Quest

A purposeful mission that helps the learner develop or transfer a capability.

Current quest types include:

- Drill.
- World.
- Discovery.
- Creation.
- Social.
- Demonstration.

### Side quest

An optional experience that adds exploration, creativity, social transfer, novelty, or real-world context without blocking main progression.

Potential side quests include:

- Visit a music shop and compare guitar tones.
- Learn a riff from a favorite artist.
- Play for a friend.
- Attend a local jam.
- Create a riff from a constraint.
- Record a loop-pedal experiment.
- Interview a musician.
- Find a song using a related progression.

## Agent architecture

The current planning system contains these agents:

### Goal Agent

Converts the learner's raw ambition and learner context into a structured `SkillGoal`.

### Research Agent

Researches how the skill is taught, identifies progression patterns, finds common failure modes, and records source provenance.

### Capability Mapper

Converts the research dossier into observable learner capabilities with prerequisites, evidence types, tiers, and failure modes.

### Progression Planner

Builds possible progression tracks and identifies shared foundations, branch points, sequencing, and pacing.

### Milestone Designer

Groups capabilities into time-bounded milestones with demonstration gates, pass criteria, failure routes, and unlocks.

### Ladder Architect

Assembles milestones into a coherent, playable ladder for the selected track.

### Quest Designer

Creates a mix of drill, transfer, and demonstration quests for a milestone.

### Recommended Track Selector

Currently selects the progression planner's recommended track automatically. Human track selection is planned for a later product UI.

### Recommended Quest Selector

Selects and displays the recommended starting quest from the generated quest set.

## Future agents

The following components are planned but are not yet part of the active runtime workflow:

- Critic.
- Placement Agent.
- Submission Agent.
- Verifier.
- Assessment Agent.
- Progression Router.
- Persistent Player Model.
- World Scout.
- Witness Service.

The future play loop will use these components to create evidence-based adaptation:

```text
Placement
  -> active quest
  -> submission
  -> verification
  -> assessment
  -> progression decision
  -> next quest
```

## Technical stack

- Python 3.13+.
- LangChain.
- LangGraph.
- Pydantic.
- OpenAI models.
- Anthropic Claude fallback through LangChain.
- Tavily for research.
- LangSmith for tracing and observability.
- LangGraph Dev / Studio for local development.

## Project structure

```text
skill-quest/
├── pyproject.toml
├── langgraph.json
├── .env
├── README.md
│
├── src/
│   └── skill_quest/
│       ├── __init__.py
│       ├── config.py
│       ├── graph.py
│       ├── nodes.py
│       ├── state.py
│       │
│       ├── goal/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       ├── research/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   ├── tools.py
│       │   └── prompts.py
│       │
│       ├── capability/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       ├── progression/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       ├── milestone/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       ├── ladder/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       ├── quest/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── agent.py
│       │   └── prompts.py
│       │
│       └── llm.py
│
└── tests/
```

The `experiments/` directory contains earlier standalone agent experiments and JSON fixtures. It is not intended to be used for normal runtime state once the application graph is active.

## State model

The LangGraph workflow uses a shared `LearnerState` object. It currently contains:

- `messages`.
- `user_request`.
- `learner_context`.
- `goal`.
- `skill_dossier`.
- `capability_map`.
- `progression_plan`.
- `milestone_design`.
- `ladder_architect`.
- `quest_set`.
- `selected_track_id`.
- `selected_quest_id`.
- `current_stage`.
- `error`.

Agent outputs are passed through graph state rather than intermediate JSON files. JSON artifacts remain useful for tests, fixtures, debugging, and evaluation datasets.

## Configuration

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
TAVILY_API_KEY=your-tavily-api-key
```

Do not commit `.env` or API keys to source control.

## Installation

Create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install -e .
```

Or, if using `uv`:

```bash
uv sync
```

Verify package imports:

```bash
python -c "import skill_quest; print(skill_quest.__file__)"
python -c "from skill_quest.graph import graph; print(graph)"
```

## Running locally

From the project root:

```bash
langgraph dev
```

The local development server exposes:

- API: `http://127.0.0.1:2024`.
- Studio: the URL printed by `langgraph dev`.
- API docs: `http://127.0.0.1:2024/docs`.

The graph is configured in `langgraph.json`.

## Current graph

The current graph is conceptually:

```text
START
  ↓
goal
  ↓
research
  ↓
capability_mapper
  ↓
progression_plan
  ↓
select_recommended_track
  ↓
milestone_design
  ↓
finalize_planning
  ↓
ladder_architect
  ↓
quest_set
  ↓
select_recommended_quest
  ↓
END
```

## Design principles

- Milestones are the unit of mastery.
- Quests are missions, not merely exercises.
- Demonstration gates matter more than self-reported completion.
- Main quests advance the selected track.
- Side quests add transfer, novelty, creativity, and identity.
- Agents propose structured artifacts.
- Pydantic models validate handoffs.
- Graph state owns runtime workflow data.
- Source IDs and provenance should be preserved.
- Policies should be enforced in code where possible.
- Human decisions should be explicit rather than hidden inside prompts.
- The system should adapt based on demonstrated capability, not only elapsed time.

## Roadmap

### Phase 1: Planning engine

Completed or in progress:

- Goal generation.
- Skill research.
- Capability mapping.
- Progression tracks.
- Milestone design.
- Ladder architecture.
- Quest generation.
- Recommended track selection.
- Recommended quest selection.
- LangGraph state passing.
- LangSmith tracing.
- OpenAI/Claude model fallback experimentation.

### Phase 2: Planning quality

- Add the Critic agent.
- Validate cross-agent references.
- Validate source provenance.
- Validate quest composition.
- Validate pacing and milestone structure.
- Create golden fixtures and regression tests.
- Produce a final `LadderPackage` artifact.

### Phase 3: Product foundation

- Add a frontend.
- Add onboarding.
- Add ladder visualization.
- Add milestone and quest cards.
- Add user accounts.
- Persist ladders and learner profiles.
- Add a database and object storage.

### Phase 4: Play Mode

- Add active quest state.
- Add quest completion.
- Add side quests.
- Add evidence submission.
- Add progress timeline.
- Add basic manual assessment.

### Phase 5: Adaptive progression

- Add Verifier.
- Add Assessment Agent.
- Add Progression Router.
- Add targeted remediation quests.
- Add a persistent Player Model.
- Add retry and plateau handling.

### Phase 6: World and social systems

- Add World Scout.
- Add location-aware side quests.
- Add social and witness workflows.
- Add seasonal and event-based opportunities.
- Add optional side-quest rewards.

### Phase 7: Portfolio product

- Deploy the application.
- Add authentication and privacy controls.
- Add evaluation dashboards.
- Add cost and latency monitoring.
- Add architecture documentation.
- Add a demo dataset.
- Add a short product walkthrough video.
- Add a technical case study for job applications.

## Portfolio value

The project is intended to demonstrate practical experience with:

- Stateful multi-agent orchestration.
- LangGraph workflow design.
- Structured outputs and schema validation.
- Retrieval and source provenance.
- Human-in-the-loop workflow design.
- Model fallback and resilience patterns.
- Product-oriented AI architecture.
- Evaluation and observability.
- Responsible AI and privacy considerations.
- Evolution from prototype to deployable application.

## Long-term success criteria

A successful product should allow a learner to:

1. Describe an ambition in natural language.
2. Receive a clear, realistic skill goal.
3. Understand the capabilities required.
4. Choose or receive a progression track.
5. See a ladder of meaningful milestones.
6. Receive one purposeful quest at a time.
7. Explore optional side quests.
8. Submit evidence of work.
9. Receive a grounded assessment.
10. Get the next best challenge based on demonstrated progress.
11. Build a portfolio of real capabilities over time.
