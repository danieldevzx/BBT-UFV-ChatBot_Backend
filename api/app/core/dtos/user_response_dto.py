from dataclasses import dataclass
from typing import Optional


@dataclass
class UserResponseDTO:
    id: str
    email: str
    name: Optional[str] = None
    perfil: Optional[str] = None
    ativo: bool = True
    created_at: Optional[str] = None
