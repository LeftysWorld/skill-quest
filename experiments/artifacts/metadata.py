from pydantic import BaseModel
from typing import Any

class ArtifactMetadata(BaseModel):
    artifact_id: str
    artifact_type: str
    produced_by: str
    model_name: str
    created_at: str
    version: int = 1


class ArtifactEnvelope(BaseModel):
    metadata: ArtifactMetadata
    payload: dict[str, Any]
