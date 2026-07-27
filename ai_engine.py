import time

from google import genai
from google.genai.errors import APIError

from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


class AIEngineError(Exception):
    """Raised when the AI engine fails to generate a summary."""
    pass


def summarize_text(text):

    if not text.strip():
        return "No text found."

    prompt = f"""
You are an expert summarization assistant.

Summarize the following document.

Requirements:
- Write a concise summary.
- Mention the main idea.
- Mention important facts.
- Keep it easy to understand.

Document:

{text}
"""

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt
            )
            return response.text

        except APIError as e:

            last_error = e

            is_overloaded = getattr(e, "code", None) == 503

            if is_overloaded and attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            raise AIEngineError(f"Gemini API error: {e}") from e

        except Exception as e:
            raise AIEngineError(f"Unexpected error: {e}") from e

    raise AIEngineError(f"Gemini API error after {MAX_RETRIES} attempts: {last_error}")