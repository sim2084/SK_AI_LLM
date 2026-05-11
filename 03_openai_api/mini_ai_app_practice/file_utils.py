import json
import tempfile
from datetime import datetime
from pathlib import Path


SAVE_DIR = Path("saved_summaries")
SAVE_DIR.mkdir(exist_ok=True)


def save_uploaded_file(uploaded_file) -> str:
    suffix = "." + uploaded_file.name.split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


def save_summary_json(title: str, lyrics: str, summary: str) -> str:
    data = {
        "title": title,
        "lyrics": lyrics,
        "summary": summary,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    safe_title = title.strip().replace(" ", "_")
    file_path = SAVE_DIR / f"{safe_title}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return str(file_path)