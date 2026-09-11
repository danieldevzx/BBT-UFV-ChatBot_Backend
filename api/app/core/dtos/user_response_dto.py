from dataclasses import dataclass
from typing import Optional


@dataclass
class UserResponseDTO:
    wa_id: str
    name: Optional[str] = None
    created_at: Optional[str] = None