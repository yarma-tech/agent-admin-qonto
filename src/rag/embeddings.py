"""Generate text embeddings via OpenAI text-embedding-3-small."""

from openai import AsyncOpenAI

from src.config import settings

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_embedding(text: str) -> list[float]:
    """Return the embedding vector for *text*."""
    response = await openai_client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding
