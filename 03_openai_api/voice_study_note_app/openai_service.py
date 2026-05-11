# OpenAI API 호출을 한 파일에 모아둔다.
# 화면(app.py)에서는 세부 API 문법을 몰라도 함수만 호출하도록 분리한다.

import json
import tempfile
from pathlib import Path
from typing import Dict, Generator

from openai import OpenAI

from config import DEFAULT_MODEL, STT_MODEL, TTS_MODEL, TTS_VOICE, MODERATION_MODEL, AUDIO_DIR

client = OpenAI()


# 브라우저에서 녹음된 음성을 STT 모델로 보내 텍스트로 변환한다.
def transcribe_audio(audio_file) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file.getvalue())
        temp_audio_path = temp_audio.name

    try:
        # TODO: 여기에 코드 작성
        with open(temp_audio_path, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=f
            )

        return transcript.text.strip()
    finally:
        Path(temp_audio_path).unlink(missing_ok=True)


# 사용자 입력이 안전한지 확인한다.
# 실제 서비스에서는 LLM 호출 전후에 안전 검사를 두는 것이 좋다.
def is_flagged(text: str) -> bool:
    if not text.strip():
        return False

    # TODO: 여기에 코드 작성
    responses = client.moderations.create(
        model=MODERATION_MODEL,
        input=text
    )
    return responses.results[0].flagged


# Structured Outputs로 학습 노트를 JSON 구조로 생성한다.
# JSON으로 받으면 화면에서 제목, 요약, 핵심 개념 등을 항목별로 안정적으로 출력할 수 있다.
def generate_study_note(transcript: str) -> Dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
            },
            "confusing_points": {
                "type": "array",
                "items": {"type": "string"},
            },
            "review_questions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "next_actions": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "title",
            "summary",
            "key_points",
            "confusing_points",
            "review_questions",
            "next_actions",
        ],
    }

    # TODO: 여기에 코드 작성
    response = client.responses.create(
        model=DEFAULT_MODEL,
        instructions=(
            "너는 초급 개발자의 학습 내용을 정리해주는 AI 학습 코치이다."
            "사용자가 말한 내용을 바탕으로 과장 없이 학습 노트를 작성한다."
            "입력에 없는 내용을 단정하지 말고, 헷갈린 부분은 복습 항목으로 정리한다."
        ),
        input=f"다음 학습 회고 내용을 학습 노트로 정리해줘. \n\n {transcript}",
        text = {
            "format" : {
                "type" : "json_schema",
                "name" : "study_note",
                "schema" : schema,
                "strict" : True
            }
        }
    )
    return json.loads(response.output_text)

# 생성된 노트를 바탕으로 짧은 복습 설명을 Streaming으로 만든다.
# Streaming은 긴 답변을 한 번에 기다리지 않고 화면에 점진적으로 보여줄 때 사용한다.
def stream_review_message(note: Dict) -> Generator[str, None, None]:
    # TODO: 여기에 코드 작성
    prompt = f"""
    다음 학습 노트를 바탕으로 초급 학습자에게 5문장 이내의 복습 메세지를 작성해줘.
    너무 장황하게 설명하지 말고, 오늘 무엇을 이해했고 다음에 무엇을 복습하면 좋을지 알려줘.

    제목: {note['title']}
    요약: {note['summary']}
    핵심 개념: {",".join(note['key_points'])}
    헷갈린 부분: {",".join(note['confusing_points'])}
    다음 할 일: {",".join(note['next_actions'])}

    """

    stream = client.responses.create(
        model=DEFAULT_MODEL,
        instructions="너는 칠절하지만 간결하게 말하는 AI 학습 코치이다.",
        input=prompt,
        stream=True
    )

    for event in stream:
        if event.type == 'response.output_text.delta':
            yield event.delta

# 복습 메시지를 TTS 모델로 변환해 음성 파일을 만든다.
def synthesize_speech(text: str) -> Path:
    output_path = AUDIO_DIR / "review_message.mp3"

    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
    ) as response :
        response.stream_to_file(output_path)

    return output_path