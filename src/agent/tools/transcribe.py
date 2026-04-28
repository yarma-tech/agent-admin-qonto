import io

from openai import AsyncOpenAI

from src.config import settings

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def transcribe_voice(audio_bytes: bytes, file_ext: str = "ogg") -> str:
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = f"voice.{file_ext}"
    response = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="fr",
    )
    return response.text
