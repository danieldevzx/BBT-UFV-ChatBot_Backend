from dataclasses import dataclass


@dataclass
class MessageResponseDTO:
    id: str
    role: str
    content: str
    created_at: str