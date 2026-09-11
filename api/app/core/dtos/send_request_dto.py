from dataclasses import dataclass
from typing import Optional


@dataclass
class SendRequestDTO:
    wa_id: str
    message: str