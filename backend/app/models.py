from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StreamSession:
    id: str
    started_at: datetime
    first_token_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    token_count: int = 0
    status: str = "active"