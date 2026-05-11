# 앱 전체에서 공통으로 사용하는 환경 설정을 관리한다.
# .env 파일에 API Key와 모델명을 분리해두면 코드에 민감 정보를 직접 쓰지 않아도 된다.

from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
MODERATION_MODEL = os.getenv("MODERATION_MODEL", "omni-moderation-latest")

BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = BASE_DIR / "notes"
AUDIO_DIR = BASE_DIR / "audio_outputs"

NOTES_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
