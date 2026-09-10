from typing import TypedDict, Optional, List
from models import Quest

class LadderArchitectState(TypedDict, total=False):
    skill: str
    ladder_template: str
    retrieved_chunks: List[str]
    draft_quests: List[Quest]
    error: Optional[str]
