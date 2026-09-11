from dataclasses import dataclass
from typing import Optional


@dataclass
class RegisterRequestDTO:
    wa_id: str
    password: str
    name: Optional[str] = None