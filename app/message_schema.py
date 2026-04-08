from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Message(BaseModel):
    message_id: int
    sender_id: int
    sender_type: str  # customer | support
    message: str
    message_type: str  # text | file | image
    file_url: Optional[str] = ""
    timestamp: datetime = datetime.utcnow()


class Ticket(BaseModel):
    ticket_id: int
    ticket_number: str
    customer_id: int
    assigned_engineer_id: Optional[int]
    status: str
    priority: str
    subject: str
    description: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    last_message_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    messages: List[Message] = []