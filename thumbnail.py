import requests
from pathlib import Path
from urllib.parse import quote

from config import POLLINATIONS_API_KEY
from ai_engine import _generate_with_fallback

THUMBNAIL_DIR = Path(__file__).resolve().parent / "thumbnails"
THUMBNAIL_DIR.mkdir(exist_ok=True)

IMAGE_MODELS = ["flux", "nanobanana", "gptimage", "zimage"]

STYLE_PRESETS = {
    "Bold Graphic": "bold graphic design, high contrast, vibrant colors, clean composition, YouTube thumbnail style",
    "Cinematic": "cinematic lighting, dramatic composition, film-still quality, rich color grading",
    "Photorealistic": "photorealistic, sharp focus, natural lighting, high detail",
    "Illustrated": "digital illustration, vibrant colors, stylized art, clean linework",
}

DEFAULT_NEGATIVE = (
    "blurry, distorted, extra limbs, deformed hands, extra fingers, "
    "watermark, text artifacts, low quality, low resolution, ugly, "
    "disfigured face"
)


def expand_prompt(rough_prompt, style):
    """
    Uses Gemini to expand a short, casual prompt into a detailed,
    well-structured image generation prompt.
    """

    style_description = STYLE_PRESETS.get(style, "")

    prompt = f"""
You are an expert AI image prompt engineer.

Expand the following rough idea into a single, detailed image
generation prompt. Include: main subject and action, setting,
lighting, camera angle/composition, and mood. Keep it to 2-3
sentences. Do not add commentary, quotes, or explanation — output
ONLY the expanded prompt text itself.

Style to incorporate: {style_description}

Rough idea:
{rough_prompt}
"""

    return _generate_with_fallback(prompt).strip()


def generate_thumbnail(
    prompt_text,
    model="flux",
    seed=None,
    width=1280,
    height=720,
):
    """
    Generates a single thumbnail image via Pollinations.ai.
    Returns the local file path on success.
    """

    full_prompt = f"{prompt_text}. Avoid: {DEFAULT_NEGATIVE}"
    encoded_prompt = quote(full_prompt)

    url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

    params = {
        "model": model,
        "width": width,
        "height": height,
    }

    if seed is not None:
        params["seed"] = seed

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    response = requests.get(url, params=params, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Image generation failed ({response.status_code}): {response.text[:200]}"
        )

    output_path = THUMBNAIL_DIR / f"thumbnail_{seed or 'default'}.png"

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def generate_thumbnail_variations(prompt_text, model="flux", count=3):
    """
    Generates several variations of the same prompt using different
    random seeds, so the user can pick the best result.
    """

    import random

    paths = []

    for i in range(count):
        seed = random.randint(1, 999999)
        path = generate_thumbnail(prompt_text, model=model, seed=seed)
        paths.append(path)

    return paths