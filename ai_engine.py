from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY


class AIEngineError(Exception):
    pass


def _get_client():
    if not OPENAI_API_KEY:
        raise AIEngineError(
            "OpenAI API key is missing. Add OPENAI_API_KEY=your_key to the .env file."
        )

    return OpenAI(api_key=OPENAI_API_KEY)


def summarize_text(text):
    if not text.strip():
        return "No readable text was found in this PDF."

    prompt = f"""
    Summarize the following text in 5 bullet points:

    {text}
    """

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    except RateLimitError as e:
        error_code = getattr(e, "code", None)
        if error_code == "insufficient_quota":
            raise AIEngineError(
                "Your OpenAI API key is valid, but the account has no available API quota. "
                "Add billing/credits on platform.openai.com or use another API key with quota."
            ) from e

        raise AIEngineError(
            "OpenAI rate limit reached. Please wait a little and try again."
        ) from e

    return response.choices[0].message.content
