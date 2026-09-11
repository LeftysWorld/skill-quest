'''
Build rule
Use the same loop for every agent:

text
1. Define input schema.
2. Define output schema.
3. Write the agent prompt.
4. Create a standalone test harness.
5. Invoke the agent with a fixed fixture.
6. Validate structured output.
7. Save the output as JSON.
8. Add one failure test.
9. Only then move to the next agent.



Group 0: Shared Contracts
Before building an agent, create the shared models that agents will exchange.

Files
text
domain/
├── enums.py
├── goals.py
├── research.py
├── capabilities.py
├── tracks.py
├── milestones.py
├── quests.py
├── assessment.py
└── packages.py

Each file should initially contain:
imports;
input schema;
output schema;
agent definition;
test fixture;
invocation;
structured-output extraction;
JSON serialization;
one basic validation check.

Once an agent works, promote its models and logic into shared modules:

text
domain/
agents/
fixtures/
workflows/
Do not share mutable runtime state between standalone experiments. Share serialized artifacts:

python
goal.model_dump_json()
dossier.model_dump_json()
capability_map.model_dump_json()
Then load them in the next file:

python
goal = SkillGoal.model_validate_json(Path("artifacts/goal.json").read_text())
This gives you explicit handoffs and makes debugging easy.
'''

