import os
from dotenv import load_dotenv

# Load .env ONLY in local dev
load_dotenv(override=True)

def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value
