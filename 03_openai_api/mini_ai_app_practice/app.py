import streamlit as st

from file_utils import save_uploaded_file, save_summary_json
from openai_api import transcribe_audio, summarize_text


st.title("음성 파일 가사 요약 앱")

title = st.text_input("노래 제목을 입력하세요")

uploaded_file = st.file_uploader(
    "음성 파일을 업로드하세요",
    type=["mp3", "wav", "m4a", "webm"]
)

summary_style = st.selectbox(
    "요약 방식",
    ["짧게 요약", "자세히 요약", "감정 중심 요약", "주제 중심 요약"]
)

if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""

if "summary" not in st.session_state:
    st.session_state.summary = ""


if st.button("STT 변환하기"):
    if uploaded_file is None:
        st.warning("음성 파일을 업로드해주세요.")
    else:
        with st.spinner("음성을 텍스트로 변환하는 중..."):
            audio_path = save_uploaded_file(uploaded_file)
            st.session_state.transcript_text = transcribe_audio(audio_path)

        st.success("STT 변환이 완료되었습니다.")


# STT 결과가 있을 때만 가사 수정 칸과 요약 버튼 표시
if st.session_state.transcript_text:
    edited_lyrics = st.text_area(
        "STT로 변환된 가사를 수정하세요",
        value=st.session_state.transcript_text,
        height=300
    )

    if st.button("요약하기"):
        if not title.strip():
            st.warning("제목을 입력해주세요.")
        elif not edited_lyrics.strip():
            st.warning("요약할 가사가 없습니다.")
        else:
            with st.spinner("수정된 가사를 요약하는 중..."):
                summary = summarize_text(
                    text=edited_lyrics,
                    summary_style=summary_style
                )

                st.session_state.summary = summary

            st.subheader("요약 결과")
            st.write(st.session_state.summary)

            file_path = save_summary_json(
                title=title,
                lyrics=edited_lyrics,
                summary=st.session_state.summary
            )

            st.success(f"JSON 파일로 저장되었습니다: {file_path}")