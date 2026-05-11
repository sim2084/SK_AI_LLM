# 학습 노트 데이터를 화면에 출력하기 좋은 형태로 다듬는 보조 함수를 둔다.
# LLM 호출과 화면 출력 사이의 간단한 가공 역할을 담당한다.

from typing import Dict

# 노트 내용을 Markdown 문자열로 변환한다.
# 저장하거나 복사할 수 있는 형태가 필요할 때 사용한다.
def note_to_markdown(note: Dict) -> str:
    key_points = "\n".join([f"- {item}" for item in note["key_points"]])
    confusing_points = "\n".join([f"- {item}" for item in note["confusing_points"]]) or "- 없음"
    review_questions = "\n".join([f"- {item}" for item in note["review_questions"]])
    next_actions = "\n".join([f"- {item}" for item in note["next_actions"]])

    return f"""# {note['title']}

## 핵심 요약
{note['summary']}

## 핵심 개념
{key_points}

## 헷갈린 부분
{confusing_points}

## 복습 질문
{review_questions}

## 다음 학습 TODO
{next_actions}
"""

def build_note_filename(title: str) -> str:
    safe_title = "".join(ch for ch in title if ch.isalnum() or ch in (" ", "_", "-"))
    safe_title = safe_title.strip().replace(" ", "_")
    return safe_title[:40] or "study_note"
