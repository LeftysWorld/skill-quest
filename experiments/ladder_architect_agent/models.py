from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID, uuid4

Difficulty = Literal["easy", "real", "wild"]
Status = Literal["offered", "in_progress", "completed", "failed"]
EvidenceType = Literal["photo", "video", "audio", "reading", "gps", "witness", "note"]

class Quest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    completion_condition: str
    evidence_required: list[EvidenceType]
    twist: str
    difficulty: Difficulty
    location: Optional[str] = None
    parent_id: Optional[UUID] = None
    ladder_id: Optional[UUID] = None
    track: Optional[str] = None
    tier: Optional[int] = Field(default=None, ge=0, le=5)
    witness_required: bool = False
    status: Status = "offered"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sources: list[str] = Field(default_factory=list)
