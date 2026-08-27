from youtube_reader import extract_youtube
from database import init_db, save_generation
from news_reader import extract_news
from ai_engine import (
    AIEngineError, summarize_text, generate_shorts_script,
    TONE_INSTRUCTIONS, OUTPUT_LANGUAGES
)
import streamlit as st
from PyPDF2 import PdfReader
import requests

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="AI Creator Hub",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------
# Main Title
# -------------------------------
st.title("🤖 AI Creator Hub")
st.markdown("---")

init_db()
# ======================================================
# MODULE 1 : PDF TEXT EXTRACTION
# ======================================================

st.header("📄 PDF Text Extraction")

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    st.success("✅ PDF Uploaded Successfully!")

    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:
        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    st.session_state["pdf_text"] = text

    st.subheader("📖 Extracted Text")

    st.text_area(
        "PDF Content",
        text,
        height=400
    )

    pdf_language = st.selectbox(
        "Output language",
        OUTPUT_LANGUAGES,
        key="lang_pdf"
    )

    if st.button("🤖 Summarize PDF"):

        with st.spinner("AI is reading the document..."):

            try:
                summary = summarize_text(text, pdf_language)
            except AIEngineError as e:
                st.error("Summary generation failed.")
                st.write(e)
                st.stop()
            except Exception as e:
                st.error("Unexpected summary error.")
                st.write(e)
                st.stop()

            save_generation("pdf", uploaded_file.name, summary)
        st.subheader("📋 AI Summary")

        st.write(summary)

# ======================================================
# MODULE 2 : NEWS ARTICLE READER
# ======================================================

st.markdown("---")

st.header("📰 News Article AI Summarizer")

news_url = st.text_input("Paste News Article URL")

if news_url:

    if st.button("📥 Read News"):

        with st.spinner("Downloading article..."):

            title, article = extract_news(news_url)

        if title is None:

            st.error(article)
            st.session_state.pop("news_title", None)
            st.session_state.pop("news_article", None)

        else:

            st.session_state["news_title"] = title
            st.session_state["news_article"] = article

    if "news_article" in st.session_state:

        st.success("Article downloaded successfully!")

        st.subheader("📰 Title")

        st.write(st.session_state["news_title"])

        st.subheader("📄 Article")

        st.text_area(
            "News Content",
            st.session_state["news_article"],
            height=300
        )

        news_language = st.selectbox(
            "Output language",
            OUTPUT_LANGUAGES,
            key="lang_news"
        )

        if st.button("🤖 Summarize News"):

            with st.spinner("AI is summarizing..."):

                try:
                    summary = summarize_text(
                        st.session_state["news_article"], news_language
                    )
                except AIEngineError as e:
                    st.error("Summary generation failed.")
                    st.write(e)
                    st.stop()
                except Exception as e:
                    st.error("Unexpected summary error.")
                    st.write(e)
                    st.stop()

                save_generation("news", news_url, summary)

            st.subheader("📋 AI Summary")

            st.write(summary)
# ======================================================
# MODULE 3 : YOUTUBE VIDEO SUMMARIZER
# ======================================================

st.markdown("---")

st.header("🎬 YouTube Video Summarizer")

youtube_url = st.text_input("Paste YouTube Video URL")

if youtube_url:

    if st.button("📥 Fetch Transcript"):

        with st.spinner("Fetching transcript..."):

            video_id, transcript = extract_youtube(youtube_url)

        if video_id is None:

            st.error(transcript)
            st.session_state.pop("yt_video_id", None)
            st.session_state.pop("yt_transcript", None)

        else:

            st.session_state["yt_video_id"] = video_id
            st.session_state["yt_transcript"] = transcript

    if "yt_transcript" in st.session_state:

        st.success("Transcript fetched successfully!")

        st.subheader("🎬 Video ID")

        st.write(st.session_state["yt_video_id"])

        st.subheader("📄 Transcript")

        st.text_area(
            "Transcript Content",
            st.session_state["yt_transcript"],
            height=300
        )

        yt_language = st.selectbox(
            "Output language",
            OUTPUT_LANGUAGES,
            key="lang_youtube"
        )

        if st.button("🤖 Summarize Video"):

            with st.spinner("AI is summarizing..."):

                try:
                    summary = summarize_text(
                        st.session_state["yt_transcript"], yt_language
                    )
                except AIEngineError as e:
                    st.error("Summary generation failed.")
                    st.write(e)
                    st.stop()
                except Exception as e:
                    st.error("Unexpected summary error.")
                    st.write(e)
                    st.stop()

                save_generation("youtube", youtube_url, summary)

            st.subheader("📋 AI Summary")

            st.write(summary)
# ======================================================
# MODULE 4 : AI SHORTS GENERATOR
# ======================================================

st.markdown("---")

st.header("🎥 AI Shorts Script Generator")

available_sources = {}

if "news_article" in st.session_state:
    available_sources["News Article"] = st.session_state["news_article"]

if "yt_transcript" in st.session_state:
    available_sources["YouTube Transcript"] = st.session_state["yt_transcript"]

if "pdf_text" in st.session_state:
    available_sources["PDF Content"] = st.session_state["pdf_text"]

if not available_sources:

    st.info(
        "No content available yet. Fetch a PDF, News article, or "
        "YouTube transcript above first, then come back here to "
        "generate a Shorts script from it."
    )

else:

    selected_source_label = st.selectbox(
        "Choose a source to generate a script from",
        list(available_sources.keys())
    )

    selected_tone = st.selectbox(
        "Choose a tone",
        list(TONE_INSTRUCTIONS.keys())
    )

    shorts_language = st.selectbox(
        "Output language",
        OUTPUT_LANGUAGES,
        key="lang_shorts"
    )

    if st.button("🎬 Generate Shorts Script"):

        source_text = available_sources[selected_source_label]

        with st.spinner("Writing your script..."):

            try:
                script = generate_shorts_script(
                    source_text, selected_tone, shorts_language
                )
            except AIEngineError as e:
                st.error("Script generation failed.")
                st.write(e)
                st.stop()
            except Exception as e:
                st.error("Unexpected error.")
                st.write(e)
                st.stop()

            save_generation(
                "shorts_script",
                f"{selected_source_label} ({selected_tone}, {shorts_language})",
                script
            )

        st.subheader("📝 Generated Script")

        st.write(script)