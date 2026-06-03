from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """
    A chat message on a task, between the client and the assigned hiver.
    Plain data + a tiny invariant (non-empty content) — the access rules
    (who may post/read) live in the use case, which knows the task's parties.
    """
    id: str
    task_id: str
    sender_id: str
    content: str
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")
        self.content = self.content.strip()
