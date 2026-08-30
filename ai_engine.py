import time

from google import genai
from google.genai.errors import APIError

from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

MAX_RETRIES_PER_MODEL = 2
RETRY_DELAY_SECONDS = 5

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]

OUTPUT_LANGUAGES = [
    "English",
    "Same as source",
    "Hindi",
    "Gujarati",
    "Spanish",
    "French",
]


class AIEngineError(Exception):
    """Raised when the AI engine fails to generate a response."""
    pass


def _generate_with_fallback(prompt):
    """
    Tries each model in FALLBACK_MODELS in order. For each model,
    retries a couple of times on transient 503 errors before moving
    on to the next model in the list.
    """

    last_error = None

    for model_name in FALLBACK_MODELS:

        for attempt in range(1, MAX_RETRIES_PER_MODEL + 1):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text

            except APIError as e:

                last_error = e
                is_overloaded = getattr(e, "code", None) == 503

                if is_overloaded and attempt < MAX_RETRIES_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue

                break

            except Exception as e:
                last_error = e
                break

    raise AIEngineError(
        f"All models failed. Last error: {last_error}"
    )


def _language_instruction(output_language, style="Respond"):
    if output_language == "Same as source":
        return f"{style} in the same language as the source content."
    return (
        f"{style} entirely in {output_language}, regardless of what "
        f"language the source content is in."
    )


def summarize_text(text, output_language="English"):

    if not text.strip():
        return "No text found."

    language_instruction = _language_instruction(output_language)

    prompt = f"""
You are an expert summarization assistant.

{language_instruction}

Summarize the following document.

Requirements:
- Write a concise summary.
- Mention the main idea.
- Mention important facts.
- Keep it easy to understand.

Document:

{text}
"""

    return _generate_with_fallback(prompt)


TONE_INSTRUCTIONS = {
    "High-energy / viral": (
        "Write in a fast-paced, punchy, high-energy style typical of viral "
        "short-form video. Use short sentences, bold claims, and urgency. "
        "Sound like a creator hyping up their audience."
    ),
    "Informative / casual": (
        "Write in a clear, friendly, conversational explainer tone. "
        "Sound like a knowledgeable friend casually walking someone "
        "through something interesting, without excessive hype."
    ),
    "Dramatic / storytelling": (
        "Write with a dramatic, narrative-driven tone, building tension "
        "and curiosity like a mini-story with a twist or reveal."
    ),
}


def generate_shorts_script(text, tone, output_language="English"):

    if not text.strip():
        return "No text found."

    tone_instruction = TONE_INSTRUCTIONS.get(
        tone, TONE_INSTRUCTIONS["Informative / casual"]
    )

    language_instruction = _language_instruction(output_language, style="Write")

    prompt = f"""
You are an expert short-form video scriptwriter, writing scripts for
YouTube Shorts, Instagram Reels, and TikTok.

Tone instructions:
{tone_instruction}

Language instructions:
{language_instruction}

Write a short-form video script based on the content below. Structure
it into these exact four labeled sections:

HOOK: A single, attention-grabbing opening line (under 15 words) that
would stop someone from scrolling in the first 2 seconds. It should
create curiosity or make a bold claim — not just state the topic.

STORY: 3-5 short sentences delivering the core content in an engaging,
easy-to-follow way. Simplify complex ideas. Keep sentences short —
this will be spoken aloud in a fast-paced video.

ENDING: 1-2 sentences that wrap up the point with a satisfying,
memorable takeaway.

CTA: A single short call-to-action line (e.g. asking viewers to
follow, comment, or share) that fits naturally with the tone and
topic — not generic or forced.

Source content:

{text}
"""

    return _generate_with_fallback(prompt)


def critique_output(original_text, generated_output, task_description):
    """
    Asks the AI to critique its own previously generated output,
    flagging weaknesses so the user can judge quality or decide
    to regenerate.
    """

    prompt = f"""
You are a strict, honest content quality reviewer.

Task that was performed:
{task_description}

Original source content (for context, truncated if long):
{original_text[:2000]}

Generated output to review:
{generated_output}

Critique the generated output. Be specific and honest, not
flattering. Structure your critique as:

STRENGTHS: 1-2 specific things done well.

WEAKNESSES: 1-2 specific, actionable issues (e.g., unclear
phrasing, missed key point, weak hook, generic CTA).

VERDICT: One line — "Good as-is" or "Consider regenerating"
with a one-sentence reason.
"""

    return _generate_with_fallback(prompt)
PLATFORM_INSTRUCTIONS = {
    "LinkedIn Post": (
        "Write a professional LinkedIn post. Use short paragraphs, "
        "a strong opening line that hooks a professional audience, "
        "and end with a thoughtful question or call-to-action to "
        "drive engagement. Keep it under 200 words. Do not use "
        "excessive hashtags — at most 3 relevant ones at the end."
    ),
    "Twitter/X Thread": (
        "Write a Twitter/X thread. Break the content into a numbered "
        "sequence of short tweets (each under 280 characters). Start "
        "with a strong hook tweet. Number each tweet like '1/', '2/', "
        "etc. Keep the tone punchy and conversational."
    ),
    "Instagram Caption": (
        "Write an engaging Instagram caption. Start with a scroll-"
        "stopping first line, use casual and relatable language, "
        "include relevant emojis sparingly, and end with 5-8 relevant "
        "hashtags on a new line."
    ),
    "Facebook Post": (
        "Write a friendly, conversational Facebook post. Slightly "
        "longer and more casual than LinkedIn, storytelling tone, "
        "encourage comments and shares."
    ),
}


def repurpose_content(text, platform, output_language="English"):

    if not text.strip():
        return "No text found."

    platform_instruction = PLATFORM_INSTRUCTIONS.get(
        platform, PLATFORM_INSTRUCTIONS["LinkedIn Post"]
    )

    language_instruction = _language_instruction(output_language, style="Write")

    prompt = f"""
You are an expert social media content strategist.

{platform_instruction}

{language_instruction}

Base the content on the following source material. Extract the
most interesting or valuable point(s) to build the post around —
don't just summarize everything.

Source content:

{text}
"""

    return _generate_with_fallback(prompt)