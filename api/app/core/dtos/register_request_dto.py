from dataclasses import dataclass
from typing import Optional


@dataclass
class RegisterRequestDTO:
    email: str
    password: str
    name: Optional[str] = None
    perfil: Optional[str] = None
