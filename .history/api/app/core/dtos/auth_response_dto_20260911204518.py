from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthResponseDTO:
    wa_id: str
    name: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None