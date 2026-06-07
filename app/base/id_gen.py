import secrets


def generate_id(prefix: str = "") -> str:
    random_part = secrets.token_urlsafe(12)
    return f"{prefix}_{random_part}" if prefix else random_part
