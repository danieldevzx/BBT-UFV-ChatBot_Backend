import re


def normalize_wa_id(wa_id: str) -> str:
    return re.sub(r"\D", "", wa_id)