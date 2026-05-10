from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    content: str
    sender: str
    timestamp: datetime = datetime.utcnow()