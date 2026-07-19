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

        st.subheader("📋 AI Summary")

        st.write(summary)

# ======================================================
# MODULE 2 : NEWS ARTICLE READER
# ======================================================

st.markdown("---")

st.header("📰 News Article Reader")

news_url = st.text_input("Paste a News Article URL")

if news_url:

    try:
        response = requests.get(news_url)

        if response.status_code == 200:

            st.success("✅ Website downloaded successfully!")

            st.write("Status Code:", response.status_code)

            st.write("Downloaded HTML Size:", len(response.text), "characters")

        else:

            st.error(f"❌ Failed to download webpage. Status Code: {response.status_code}")

    except Exception as e:

        st.error("❌ An error occurred while connecting.")

        st.write(e)
