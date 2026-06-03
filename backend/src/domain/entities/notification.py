from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    """
    A delivered in-app notification — read model for the notification feed/bell.
    Created by the INotificationPort (push side); read back via INotificationRepository.
    """
    id: str
    user_id: str
    title: str
    body: str
    data: dict = field(default_factory=dict)
    is_read: bool = False
    sent_at: datetime = field(default_factory=datetime.utcnow)
