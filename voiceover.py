import re
import asyncio
from pathlib import Path

import edge_tts

VOICEOVER_DIR = Path(__file__).resolve().parent / "voiceovers"
VOICEOVER_DIR.mkdir(exist_ok=True)

# A curated selection of good-quality free voices per language.
# Format: "Display Name": "edge-tts voice ID"
VOICE_OPTIONS = {
    "English": {
        "Aria (Female, US)": "en-US-AriaNeural",
        "Guy (Male, US)": "en-US-GuyNeural",
        "Sonia (Female, UK)": "en-GB-SoniaNeural",
    },
    "Hindi": {
        "Swara (Female)": "hi-IN-SwaraNeural",
        "Madhur (Male)": "hi-IN-MadhurNeural",
    },
    "Gujarati": {
        "Dhwani (Female)": "gu-IN-DhwaniNeural",
        "Niranjan (Male)": "gu-IN-NiranjanNeural",
    },
    "Spanish": {
        "Elvira (Female)": "es-ES-ElviraNeural",
        "Alvaro (Male)": "es-ES-AlvaroNeural",
    },
    "French": {
        "Denise (Female)": "fr-FR-DeniseNeural",
        "Henri (Male)": "fr-FR-HenriNeural",
    },
}


def _clean_for_speech(text):
    """
    Removes markdown-style labels (HOOK:, STORY:, etc.) and formatting
    so the voiceover doesn't literally say 'H O O K colon'.
    """
    text = re.sub(r"\b(HOOK|STORY|ENDING|CTA)\s*:", "", text)
    text = re.sub(r"\*\*|\*|#", "", text)
    return text.strip()


def _rate_string(speed_percent):
    """
    Converts a speed percentage (e.g. 100 = normal, 130 = 30% faster,
    70 = 30% slower) into edge-tts's rate format (e.g. '+30%', '-30%').
    """
    diff = speed_percent - 100
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff}%"


async def _synthesize(text, voice_id, rate_string, output_path):
    communicate = edge_tts.Communicate(text, voice_id, rate=rate_string)
    await communicate.save(str(output_path))


def generate_voiceover(text, voice_id, speed_percent=100, filename="voiceover"):
    """
    Converts text to speech using edge-tts and saves it as an MP3 file.
    Returns the file path on success, raises an exception on failure.
    """

    clean_text = _clean_for_speech(text)

    if not clean_text:
        raise ValueError("No text available to convert to speech.")

    output_path = VOICEOVER_DIR / f"{filename}.mp3"
    rate_string = _rate_string(speed_percent)

    try:
        asyncio.run(_synthesize(clean_text, voice_id, rate_string, output_path))
    except Exception as e:
        raise RuntimeError(f"Text-to-speech failed: {e}") from e

    return output_path