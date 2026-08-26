import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


def _extract_video_id(url):
    """
    Extracts the YouTube video ID from common URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """

    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"shorts\/([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extract_youtube(url):
    """
    Fetches the transcript for a YouTube video URL.
    Returns (video_id, transcript_text) on success,
    or (None, error_message) on failure.
    """

    video_id = _extract_video_id(url)

    if video_id is None:
        return None, "Error: Could not extract a valid video ID from that URL."

    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)

        full_text = " ".join(
            snippet.text for snippet in fetched_transcript
        )

        return video_id, full_text

    except TranscriptsDisabled:
        return None, "Error: Transcripts are disabled for this video."
    except NoTranscriptFound:
        return None, "Error: No transcript available for this video."
    except VideoUnavailable:
        return None, "Error: This video is unavailable."
    except Exception as e:
        return None, f"Error: {e}"