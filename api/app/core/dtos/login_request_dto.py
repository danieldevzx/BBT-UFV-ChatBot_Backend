from dataclasses import dataclass


@dataclass
class LoginRequestDTO:
    wa_id: str
    password: str