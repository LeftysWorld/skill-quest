# store.py
from sqlmodel import SQLModel, Field, create_engine, Session
from models import Quest as QuestModel
from uuid import UUID
from datetime import datetime

class QuestRow(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    title: str
    completion_condition: str
    evidence_required: str  # JSON-encoded list
    twist: str
    difficulty: str
    location: str | None = None
    parent_id: UUID | None = None
    ladder_id: UUID | None = None
    track: str | None = None
    tier: int | None = None
    witness_required: bool = False
    status: str = "offered"
    created_at: datetime
    sources: str  # JSON-encoded list

engine = create_engine("sqlite:///quests.db")
SQLModel.metadata.create_all(engine)

def save_quests(quests: list[QuestModel], ladder_id: UUID | None = None):
    with Session(engine) as session:
        for q in quests:
            row = QuestRow(
                id=q.id,
                title=q.title,
                completion_condition=q.completion_condition,
                evidence_required=str(q.evidence_required),
                twist=q.twist,
                difficulty=q.difficulty,
                location=q.location,
                parent_id=q.parent_id,
                ladder_id=ladder_id,
                track=q.track,
                tier=q.tier,
                witness_required=q.witness_required,
                status=q.status,
                created_at=q.created_at,
                sources=str(q.sources),
            )
            session.add(row)
        session.commit()
