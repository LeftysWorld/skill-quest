import os
from datetime import datetime
from typing import List, Literal, Optional, TypedDict
from uuid import UUID, uuid4

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent

# --- config ---
load_dotenv("../.env")

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)

# --- domain types ---
class Quest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    completion_condition: str
    evidence_required: list[Literal["photo", "video", "audio", "reading", "gps", "witness", "note"]]
    twist: str
    difficulty: Literal["easy", "real", "wild"]
    location: Optional[str] = None
    parent_id: Optional[UUID] = None
    ladder_id: Optional[UUID] = None
    track: Optional[str] = None
    tier: Optional[int] = Field(default=None, ge=0, le=5)
    witness_required: bool = False
    status: Literal["offered", "in_progress", "completed", "failed"] = "offered"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sources: list[str] = Field(default_factory=list)


# --- retrieval ---
reader = SimpleDirectoryReader("syllabi/")
documents = reader.load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=3)


def retrieve_curriculum(skill: str, query: str) -> list[str]:
    results = query_engine.query(f"{skill}: {query}")
    return [node.text for node in results.source_nodes]


# --- agent ---
architect_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=list[Quest],
    instructions="""
        You are a Ladder Architect for real-world skill ladders.
        You must return ONLY a JSON list of Quest objects.
        Every quest must have: title, completion_condition, evidence_required, twist, difficulty.
        Use the provided ladder template and retrieved curriculum chunks as sources.
        Do not invent places or resources; only use what is provided.
        """,
)


# --- graph ---
class LadderArchitectState(TypedDict, total=False):
    skill: str
    ladder_template: str
    retrieved_chunks: List[str]
    draft_quests: List[Quest]
    error: Optional[str]


def ladder_architect_node(state: LadderArchitectState, config: RunnableConfig) -> LadderArchitectState:
    skill = state.get("skill", "unknown")
    template = state.get("ladder_template", "")
    chunks = retrieve_curriculum(skill, "progression, tiers, safety")
    prompt = f"""
        Skill: {skill}
        Ladder template:
        {template}
        
        Retrieved curriculum chunks:
        {chr(10).join(chunks)}
        
        Task: Generate Quest objects for the next appropriate nodes.
        Return ONLY a JSON list of Quest objects.
    """

    try:
        result = architect_agent.run_sync(prompt)
        return {"draft_quests": result.output, "retrieved_chunks": chunks}
    except Exception as e:
        return {"error": str(e)}


builder = StateGraph(LadderArchitectState)
builder.add_node("architect", ladder_architect_node)
builder.add_edge(START, "architect")
builder.add_edge("architect", END)
graph = builder.compile()


# --- entry ---
FERMENTATION_TEMPLATE = """
    Six tiers:
        0 Culture (buy starter from person)
        1 First batch
        2 Tracks (Bottle, Grain, Koji, Orchard)
        3 World nodes (brewery/club visit)
        4 Long ones (miso, sake)
        5 Give it away
    """

INITIAL_STATE = {
    "skill": "fermentation",
    "ladder_template": FERMENTATION_TEMPLATE,
}


if __name__ == "__main__":
    result = graph.invoke(INITIAL_STATE)
    print(result.get("draft_quests", []))
