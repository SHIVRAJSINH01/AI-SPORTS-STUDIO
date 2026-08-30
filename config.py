import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _clean_env_value(value):
    if value is None:
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1].strip()

    return value or None


OPENAI_API_KEY = _clean_env_value(os.getenv("OPENAI_API_KEY"))
GEMINI_API_KEY = _clean_env_value(os.getenv("GEMINI_API_KEY"))
POLLINATIONS_API_KEY = _clean_env_value(os.getenv("POLLINATIONS_API_KEY"))