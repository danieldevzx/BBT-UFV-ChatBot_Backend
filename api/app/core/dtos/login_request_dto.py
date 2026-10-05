from dataclasses import dataclass


@dataclass
class LoginRequestDTO:
    email: str
    password: str
