from database import init_db, save_generation
from news_reader import extract_news
from ai_engine import AIEngineError, summarize_text
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

    st.subheader("📖 Extracted Text")

    st.text_area(
        "PDF Content",
        text,
        height=400
    )

    if st.button("🤖 Summarize PDF"):

        with st.spinner("AI is reading the document..."):

            try:
                summary = summarize_text(text)
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

        if st.button("🤖 Summarize News"):

            with st.spinner("AI is summarizing..."):

                try:
                    summary = summarize_text(st.session_state["news_article"])
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