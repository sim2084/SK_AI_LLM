# 생성된 학습 노트를 로컬 파일로 저장하고 최근 노트를 조회한다.
# DB 없이도 저장 흐름을 경험할 수 있도록 JSON 파일 기반으로 구성한다.

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import NOTES_DIR
from note_service import build_note_filename


# 학습 노트를 notes 폴더에 JSON 파일로 저장한다.
def save_note(note: Dict, transcript: str, review_message: str = "") -> Path:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_time}_{build_note_filename(note['title'])}.json"
    path = NOTES_DIR / filename

    payload = {
        "created_at": created_at,
        "transcript": transcript,
        "note": note,
        "review_message": review_message,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path

# 최근 생성된 학습 노트를 최신순으로 불러온다.
def load_recent_notes(limit: int = 3) -> List[Dict]:
    files = sorted(NOTES_DIR.glob("*.json"), reverse=True)
    notes = []

    for path in files[:limit]:
        with open(path, "r", encoding="utf-8") as f:
            notes.append(json.load(f))

    return notes

# [확장 실습] 파일 저장 대신 SQLite나 CSV로 바꾸면 검색, 필터링, 통계 기능을 붙일 수 있다.
