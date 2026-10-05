from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthResponseDTO:
    email: str
    name: Optional[str] = None
    perfil: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None
