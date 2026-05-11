import os
from dotenv import load_dotenv
from openai import OpenAI

from prompt import make_summary_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file
        )

    return transcript.text


def summarize_text(
    title: str,
    text: str,
    summary_style: str
) -> str:

    prompt = make_summary_prompt(
        title=title,
        text=text,
        summary_style=summary_style
    )

    response = client.responses.create(
        model="gpt-5.2",
        input=prompt
    )

    return response.output_text