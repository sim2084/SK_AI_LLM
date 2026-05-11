# Streamlit 화면을 구성하는 메인 파일
# 이 앱은 음성 입력을 학습 노트로 정리하고, 짧은 복습 메시지를 음성으로 들려준다.

import streamlit as st

from config import OPENAI_API_KEY
from note_service import note_to_markdown
from openai_service import (
    generate_study_note,
    is_flagged,
    stream_review_message,
    synthesize_speech,
    transcribe_audio,
)
from storage_service import load_recent_notes, save_note


# 페이지 기본 설정과 API Key 확인
st.set_page_config(
    page_title="Voice Study Note",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ Voice Study Note")
st.caption("말로 남긴 학습 회고를 구조화된 복습 노트로 정리하는 앱")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")
    st.stop()


# Streamlit은 위젯 조작마다 스크립트가 다시 실행되므로 session_state에 중간 결과를 보관한다.
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "note" not in st.session_state:
    st.session_state.note = None
if "review_message" not in st.session_state:
    st.session_state.review_message = ""


# 브라우저 마이크로 음성을 녹음한다.
# st.audio_input은 사용자가 마이크 권한을 허용하면 녹음 파일을 반환한다.
st.subheader("1. 오늘 배운 내용을 말해보세요")
audio_value = st.audio_input("녹음 버튼을 누르고 학습 내용을 말해보세요.")

if audio_value and st.button("음성을 텍스트로 변환"):
    with st.spinner("STT 변환 중..."):
        st.session_state.transcript = transcribe_audio(audio_value)


# STT 결과를 확인하고 필요하면 직접 수정할 수 있게 한다.
# 실제 음성 인식 결과는 틀릴 수 있으므로 사용자가 수정할 수 있는 입력창을 둔다.
st.subheader("2. STT 결과 확인")
st.session_state.transcript = st.text_area(
    "변환된 텍스트를 확인하고 필요하면 수정하세요.",
    value=st.session_state.transcript,
    height=160,
    placeholder="예: 오늘은 STT, TTS를 배웠다...",
)


# 입력 텍스트를 Structured Outputs로 학습 노트 형태로 변환한다.
st.subheader("3. 학습 노트 생성")

if st.button("학습 노트 만들기", type="primary"):
    transcript = st.session_state.transcript.strip()

    if not transcript:
        st.warning("먼저 음성을 입력하거나 텍스트를 작성하세요.")
    elif is_flagged(transcript):
        st.warning("입력 내용이 안전 정책에 의해 차단되었습니다. 학습 회고 내용으로 다시 작성해 주세요.")
    else:
        with st.spinner("학습 노트 생성 중..."):
            st.session_state.note = generate_study_note(transcript)
            st.session_state.review_message = ""


# 생성된 노트를 항목별로 출력한다.
# JSON 구조로 받았기 때문에 화면에서 원하는 위치에 안정적으로 배치할 수 있다.
if st.session_state.note:
    note = st.session_state.note

    st.divider()
    st.subheader("생성된 학습 노트")
    st.markdown(f"### {note['title']}")
    st.write(note["summary"])

    st.markdown("#### 핵심 개념")
    for item in note["key_points"]:
        st.markdown(f"- {item}")

    st.markdown("#### 헷갈린 부분")
    if note["confusing_points"]:
        for item in note["confusing_points"]:
            st.markdown(f"- {item}")
    else:
        st.markdown("- 없음")

    st.markdown("#### 복습 질문")
    for item in note["review_questions"]:
        st.markdown(f"- {item}")

    st.markdown("#### 다음 학습 TODO")
    for item in note["next_actions"]:
        st.markdown(f"- {item}")

    with st.expander("Markdown으로 보기"):
        st.code(note_to_markdown(note), language="markdown")

    
    # 복습 메시지를 Streaming으로 출력한다.
    # 완성된 노트와 별도로 짧은 코칭 메시지를 실시간 생성해 UX를 확인한다.
    if st.button("짧은 복습 메시지 생성"):
        st.markdown("#### 짧은 복습 메시지")
        placeholder = st.empty()
        chunks = []

        for chunk in stream_review_message(note):
            chunks.append(chunk)
            placeholder.markdown("".join(chunks))

        st.session_state.review_message = "".join(chunks)

    
    # 복습 메시지를 TTS로 변환해 오디오로 재생한다.
    if st.session_state.review_message:
        if st.button("복습 메시지 음성으로 듣기"):
            with st.spinner("TTS 생성 중..."):
                audio_path = synthesize_speech(st.session_state.review_message)
            st.audio(str(audio_path))

    
    # 생성된 노트와 원문, 복습 메시지를 저장한다.
    if st.button("학습 노트 저장"):
        save_path = save_note(
            note=st.session_state.note,
            transcript=st.session_state.transcript,
            review_message=st.session_state.review_message,
        )
        st.success(f"저장 완료: {save_path.name}")


# 최근 노트 조회는 기본 기능으로 제공하되, 검색/필터링/통계로 확장할 수 있다.
st.divider()
st.subheader("최근 생성한 노트")

recent_notes = load_recent_notes(limit=3)

if not recent_notes:
    st.caption("아직 저장된 노트가 없습니다.")
else:
    for item in recent_notes:
        note = item["note"]
        with st.expander(f"{item['created_at']} · {note['title']}"):
            st.write(note["summary"])
            st.markdown("복습 질문")
            for question in note["review_questions"]:
                st.markdown(f"- {question}")


# [확장 실습] 
# 1. 저장된 노트에서 복습 질문만 따로 모아 퀴즈 화면 만들기
# 2. 헷갈린 부분을 기준으로 다음 학습 계획 생성하기
# 3. Function Calling으로 save_note, get_recent_notes 함수를 도구 호출 방식으로 바꾸기
# 4. 노트 검색 기능 또는 태그 기능 추가하기
