import streamlit as st
from PyPDF2 import PdfReader
import requests

from database import init_db, save_generation, get_history_by_type, get_history
from news_reader import extract_news
from youtube_reader import extract_youtube
from voiceover import generate_voiceover, VOICE_OPTIONS
from thumbnail import (
    expand_prompt, generate_thumbnail_variations,
    STYLE_PRESETS, IMAGE_MODELS
)
from ai_engine import (
    AIEngineError, summarize_text, generate_shorts_script,
    TONE_INSTRUCTIONS, OUTPUT_LANGUAGES, critique_output,
    continue_advisor_chat, repurpose_content, PLATFORM_INSTRUCTIONS,
    combine_and_summarize
)

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


def render_advisor_chat(chat_key, original_text, generated_output, task_description):
    """
    Renders a full conversational advisor: a button that starts the
    conversation with a critique report as the opening message, then
    an ongoing chat interface for further discussion.
    """

    if chat_key not in st.session_state:

        if st.button("💬 Discuss & Improve", key=f"start_{chat_key}"):
            with st.spinner("Generating initial review..."):
                try:
                    initial_critique = critique_output(
                        original_text, generated_output, task_description
                    )
                except AIEngineError as e:
                    st.error("Failed to start conversation.")
                    st.write(e)
                    st.stop()

            st.session_state[chat_key] = [
                {"role": "assistant", "content": initial_critique}
            ]
            st.rerun()

    if chat_key in st.session_state:

        st.subheader("💬 Content Advisor")

        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input(
            "Ask how to improve this...", key=f"input_{chat_key}"
        )

        if user_input:

            st.session_state[chat_key].append(
                {"role": "user", "content": user_input}
            )

            with st.spinner("Thinking..."):
                try:
                    reply = continue_advisor_chat(
                        original_text, task_description,
                        st.session_state[chat_key]
                    )
                except AIEngineError as e:
                    reply = f"Sorry, something went wrong: {e}"

            st.session_state[chat_key].append(
                {"role": "assistant", "content": reply}
            )

            st.rerun()


# ======================================================
# MODULE 1 : PDF TEXT EXTRACTION
# ======================================================

st.header("📄 PDF Text Extraction")

recent_pdfs = get_history_by_type("pdf", limit=5)

if recent_pdfs:
    with st.expander(f"🕒 Recent PDFs ({len(recent_pdfs)})"):
        for entry in recent_pdfs:
            _, _, input_data, _, created_at = entry
            st.code(input_data, language=None)
            st.caption(created_at)

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

        st.session_state["pdf_summary"] = summary

    if "pdf_summary" in st.session_state:

        st.subheader("📋 AI Summary")
        st.write(st.session_state["pdf_summary"])

        render_advisor_chat(
            "pdf_advisor_chat",
            text,
            st.session_state["pdf_summary"],
            "Summarized a PDF document"
        )

# ======================================================
# MODULE 2 : NEWS ARTICLE READER
# ======================================================

st.markdown("---")

st.header("📰 News Article AI Summarizer")

recent_news = get_history_by_type("news", limit=5)

if recent_news:
    with st.expander(f"🕒 Recent Articles ({len(recent_news)})"):
        for idx, entry in enumerate(recent_news):
            _, _, input_data, _, created_at = entry
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(input_data, language=None)
                st.caption(created_at)
            with col2:
                if st.button("🔁 Use", key=f"reuse_news_{idx}"):
                    st.session_state["news_url_input"] = input_data
                    st.rerun()

news_url = st.text_input(
    "Paste News Article URL",
    key="news_url_input"
)

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

            st.session_state["news_summary"] = summary

        if "news_summary" in st.session_state:

            st.subheader("📋 AI Summary")
            st.write(st.session_state["news_summary"])

            render_advisor_chat(
                "news_advisor_chat",
                st.session_state["news_article"],
                st.session_state["news_summary"],
                "Summarized a news article"
            )
# ======================================================
# MODULE 3 : YOUTUBE VIDEO SUMMARIZER
# ======================================================

st.markdown("---")

st.header("🎬 YouTube Video Summarizer")

recent_youtube = get_history_by_type("youtube", limit=5)

if recent_youtube:
    with st.expander(f"🕒 Recent Videos ({len(recent_youtube)})"):
        for idx, entry in enumerate(recent_youtube):
            _, _, input_data, _, created_at = entry
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(input_data, language=None)
                st.caption(created_at)
            with col2:
                if st.button("🔁 Use", key=f"reuse_yt_{idx}"):
                    st.session_state["yt_url_input"] = input_data
                    st.rerun()

youtube_url = st.text_input(
    "Paste YouTube Video URL",
    key="yt_url_input"
)

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

            st.session_state["yt_summary"] = summary

        if "yt_summary" in st.session_state:

            st.subheader("📋 AI Summary")
            st.write(st.session_state["yt_summary"])

            render_advisor_chat(
                "youtube_advisor_chat",
                st.session_state["yt_transcript"],
                st.session_state["yt_summary"],
                "Summarized a YouTube video transcript"
            )
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

        st.session_state["shorts_script"] = script
        st.session_state["shorts_source_text"] = source_text

    if "shorts_script" in st.session_state:

        st.subheader("📝 Generated Script")
        st.write(st.session_state["shorts_script"])

        render_advisor_chat(
            "shorts_advisor_chat",
            st.session_state["shorts_source_text"],
            st.session_state["shorts_script"],
            "Generated a short-form video script (Hook/Story/Ending/CTA)"
        )
# ======================================================
# MODULE 5 : AI VOICEOVER
# ======================================================

st.markdown("---")

st.header("🔊 AI Voiceover Generator")

voiceover_sources = {}

if "news_summary" in st.session_state:
    voiceover_sources["News Summary"] = st.session_state["news_summary"]

if "yt_summary" in st.session_state:
    voiceover_sources["YouTube Summary"] = st.session_state["yt_summary"]

if "pdf_summary" in st.session_state:
    voiceover_sources["PDF Summary"] = st.session_state["pdf_summary"]

if "shorts_script" in st.session_state:
    voiceover_sources["Shorts Script"] = st.session_state["shorts_script"]

if not voiceover_sources:

    st.info(
        "No content available yet. Generate a summary or Shorts "
        "script above first, then come back here to create a "
        "voiceover from it."
    )

else:

    selected_vo_label = st.selectbox(
        "Choose content to convert to voiceover",
        list(voiceover_sources.keys())
    )

    editable_text = st.text_area(
        "Edit the text before generating voiceover (optional)",
        voiceover_sources[selected_vo_label],
        height=200,
        key="vo_editable_text"
    )

    vo_language = st.selectbox(
        "Voiceover language",
        list(VOICE_OPTIONS.keys()),
        key="lang_voiceover"
    )

    vo_voice_label = st.selectbox(
        "Choose a voice",
        list(VOICE_OPTIONS[vo_language].keys()),
        key="voice_choice"
    )

    vo_speed = st.slider(
        "Speed (%)",
        min_value=70,
        max_value=150,
        value=100,
        step=10,
        key="vo_speed"
    )

    if st.button("🔊 Generate Voiceover"):

        voice_id = VOICE_OPTIONS[vo_language][vo_voice_label]

        with st.spinner("Generating voiceover..."):

            try:
                audio_path = generate_voiceover(
                    editable_text, voice_id, vo_speed,
                    filename="latest_voiceover"
                )
            except (ValueError, RuntimeError) as e:
                st.error("Voiceover generation failed.")
                st.write(e)
                st.stop()

            save_generation(
                "voiceover",
                f"{selected_vo_label} ({vo_language}, {vo_voice_label}, {vo_speed}%)",
                str(audio_path)
            )

        st.success("Voiceover generated!")

        st.audio(str(audio_path))

        with open(audio_path, "rb") as f:
            st.download_button(
                "⬇️ Download MP3",
                f,
                file_name="voiceover.mp3",
                mime="audio/mpeg"
            )
# ======================================================
# MODULE 6 : AI THUMBNAIL GENERATOR
# ======================================================

st.markdown("---")

st.header("🖼️ AI Thumbnail Generator")

thumb_prompt = st.text_area(
    "Describe your thumbnail idea",
    placeholder="e.g. Messi scores a goal in the 92nd minute, dramatic stadium lighting",
    key="thumb_prompt_input"
)

thumb_style = st.selectbox(
    "Style",
    list(STYLE_PRESETS.keys()),
    key="thumb_style"
)

thumb_model = st.selectbox(
    "Image model",
    IMAGE_MODELS,
    key="thumb_model"
)

if thumb_prompt:

    if st.button("✨ Enhance My Prompt"):

        with st.spinner("Expanding your idea into a detailed prompt..."):
            try:
                expanded = expand_prompt(thumb_prompt, thumb_style)
            except AIEngineError as e:
                st.error("Prompt expansion failed.")
                st.write(e)
                st.stop()

        st.session_state["thumb_expanded_prompt"] = expanded

    if "thumb_expanded_prompt" in st.session_state:

        st.subheader("📝 Expanded Prompt")

        final_prompt = st.text_area(
            "Edit if needed before generating",
            st.session_state["thumb_expanded_prompt"],
            height=100,
            key="thumb_final_prompt"
        )

        if st.button("🖼️ Generate Thumbnail Variations"):

            with st.spinner("Generating 3 variations..."):
                try:
                    image_paths = generate_thumbnail_variations(
                        final_prompt, model=thumb_model, count=3
                    )
                except RuntimeError as e:
                    st.error("Thumbnail generation failed.")
                    st.write(e)
                    st.stop()

                save_generation(
                    "thumbnail",
                    thumb_prompt,
                    f"{len(image_paths)} variations generated"
                )

            st.session_state["thumb_image_paths"] = image_paths

    if "thumb_image_paths" in st.session_state:

        st.subheader("🖼️ Choose Your Favorite")

        cols = st.columns(len(st.session_state["thumb_image_paths"]))

        for idx, (col, path) in enumerate(
            zip(cols, st.session_state["thumb_image_paths"])
        ):
            with col:
                st.image(str(path), use_container_width=True)
                with open(path, "rb") as f:
                    st.download_button(
                        f"⬇️ Download #{idx + 1}",
                        f,
                        file_name=f"thumbnail_{idx + 1}.png",
                        mime="image/png",
                        key=f"download_thumb_{idx}"
                    )
# ======================================================
# MODULE 7 : CONTENT REPURPOSING
# ======================================================

st.markdown("---")

st.header("🔁 Content Repurposing")

repurpose_sources = {}

if "news_summary" in st.session_state:
    repurpose_sources["News Summary"] = st.session_state["news_summary"]

if "yt_summary" in st.session_state:
    repurpose_sources["YouTube Summary"] = st.session_state["yt_summary"]

if "pdf_summary" in st.session_state:
    repurpose_sources["PDF Summary"] = st.session_state["pdf_summary"]

if not repurpose_sources:

    st.info(
        "No content available yet. Generate a summary above first, "
        "then come back here to repurpose it for social media."
    )

else:

    repurpose_source_label = st.selectbox(
        "Choose content to repurpose",
        list(repurpose_sources.keys()),
        key="repurpose_source"
    )

    repurpose_platform = st.selectbox(
        "Target platform",
        list(PLATFORM_INSTRUCTIONS.keys()),
        key="repurpose_platform"
    )

    repurpose_language = st.selectbox(
        "Output language",
        OUTPUT_LANGUAGES,
        key="lang_repurpose"
    )

    if st.button("🔁 Repurpose Content"):

        source_text = repurpose_sources[repurpose_source_label]

        with st.spinner(f"Writing for {repurpose_platform}..."):

            try:
                repurposed = repurpose_content(
                    source_text, repurpose_platform, repurpose_language
                )
            except AIEngineError as e:
                st.error("Repurposing failed.")
                st.write(e)
                st.stop()

            save_generation(
                "repurposed_content",
                f"{repurpose_source_label} → {repurpose_platform}",
                repurposed
            )

        st.session_state["repurposed_output"] = repurposed

    if "repurposed_output" in st.session_state:

        st.subheader(f"📱 {repurpose_platform} Version")
        st.write(st.session_state["repurposed_output"])
# ======================================================
# MODULE 8 : FULL ACTIVITY HISTORY
# ======================================================

st.markdown("---")

st.header("📜 Full Activity History")

full_history = get_history(limit=15)

if not full_history:

    st.info("No activity yet. Start using any module above to build your history.")

else:

    full_history = list(reversed(full_history))

    step_labels = {
        "pdf": "📄 PDF",
        "news": "📰 News",
        "youtube": "🎬 YouTube",
        "shorts_script": "🎥 Shorts",
        "voiceover": "🔊 Voice",
        "thumbnail": "🖼️ Thumb",
        "repurposed_content": "🔁 Post",
        "combined_summary": "🧩 Combined",
    }

    show_full = st.checkbox("Show full history (all steps)", key="show_full_history")

    visible_history = full_history if show_full else full_history[-5:]

    hidden_count = len(full_history) - len(visible_history)

    if hidden_count > 0:
        st.caption(f"Showing last {len(visible_history)} of {len(full_history)} steps.")

    box_parts = []
    for i, entry in enumerate(visible_history):
        source_type = entry[1]
        label = step_labels.get(source_type, source_type)

        box_parts.append(
            f'<div style="display:inline-block; padding:10px 16px; margin:4px; '
            f'border-radius:8px; background-color:#2b313e; color:white; '
            f'font-size:14px; text-align:center; border:1px solid #444;">'
            f'{i+1}. {label}</div>'
        )

    arrow = '<span style="font-size:20px; color:#888; margin:0 4px;">→</span>'
    diagram_html = arrow.join(box_parts)

    st.markdown(
        f'<div style="display:flex; flex-wrap:wrap; align-items:center;">{diagram_html}</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    for i, entry in enumerate(visible_history):
        _, source_type, input_data, output_data, created_at = entry

        label = step_labels.get(source_type, source_type)

        with st.expander(f"{i+1}. {label} — {created_at}"):
            st.write(f"**Source/Input:** {input_data}")
            st.write("**Output:**")
            st.write(output_data)
# ======================================================
# MODULE 9 : MULTI-SOURCE COMBINED SUMMARY
# ======================================================

st.markdown("---")

st.header("🧩 Multi-Source Combined Summary")

combine_sources = {}

if "news_article" in st.session_state:
    combine_sources["News Article"] = st.session_state["news_article"]

if "yt_transcript" in st.session_state:
    combine_sources["YouTube Transcript"] = st.session_state["yt_transcript"]

if "pdf_text" in st.session_state:
    combine_sources["PDF Content"] = st.session_state["pdf_text"]

if len(combine_sources) < 2:

    st.info(
        "Fetch at least 2 sources above (any combination of PDF, "
        "News, or YouTube) to combine them into one summary."
    )

else:

    selected_labels = st.multiselect(
        "Choose 2 or more sources to combine",
        list(combine_sources.keys()),
        default=list(combine_sources.keys())
    )

    combine_language = st.selectbox(
        "Output language",
        OUTPUT_LANGUAGES,
        key="lang_combine"
    )

    if len(selected_labels) >= 2:

        if st.button("🧩 Combine & Summarize"):

            chosen = {
                label: combine_sources[label] for label in selected_labels
            }

            with st.spinner("Synthesizing sources..."):

                try:
                    combined = combine_and_summarize(chosen, combine_language)
                except AIEngineError as e:
                    st.error("Combination failed.")
                    st.write(e)
                    st.stop()

                save_generation(
                    "combined_summary",
                    " + ".join(selected_labels),
                    combined
                )

            st.session_state["combined_summary"] = combined

    elif selected_labels:

        st.warning("Select at least 2 sources to combine.")

    if "combined_summary" in st.session_state:

        st.subheader("🧩 Combined Summary")
        st.write(st.session_state["combined_summary"])