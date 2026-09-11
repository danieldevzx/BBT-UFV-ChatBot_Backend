from dataclasses import dataclass


@dataclass
class ConversationResponseDTO:
    id: str
    wa_id: str
    status: str
    message_count: int
    created_at: str
    updated_at: str