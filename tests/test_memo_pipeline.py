"""Tests for the voice memo → RAG pipeline."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# process_voice_memo tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memo_indexed_when_business_entity(mock_session, tenant_id):
    """Voice with business entity → indexed in RAG + summary returned."""
    with (
        patch("src.telegram.handlers.index_text") as mock_index,
        patch("src.telegram.handlers.anthropic") as mock_anthropic,
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Note : RDV KADO, budget 5K")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        from src.telegram.handlers import process_voice_memo

        result = await process_voice_memo(mock_session, tenant_id, "RDV KADO budget 5000 euros")

    assert result is not None
    assert "Note" in result
    mock_index.assert_called_once()


@pytest.mark.asyncio
async def test_short_message_not_indexed(mock_session, tenant_id):
    """Short message without entity → not indexed, returns None."""
    with patch("src.telegram.handlers.index_text") as mock_index:
        from src.telegram.handlers import process_voice_memo

        result = await process_voice_memo(mock_session, tenant_id, "ok merci")

    assert result is None
    mock_index.assert_not_called()


@pytest.mark.asyncio
async def test_long_message_indexed(mock_session, tenant_id):
    """Long message without explicit entity → indexed because word count > 5."""
    with (
        patch("src.telegram.handlers.index_text") as mock_index,
        patch("src.telegram.handlers.anthropic") as mock_anthropic,
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Note : message long sans entité particulière")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        from src.telegram.handlers import process_voice_memo

        result = await process_voice_memo(
            mock_session,
            tenant_id,
            "Voici un message sans entité particulière mais suffisamment long",
        )

    assert result is not None
    mock_index.assert_called_once()


@pytest.mark.asyncio
async def test_index_text_called_with_correct_args(mock_session, tenant_id):
    """index_text must be called with session, tenant_id and transcription."""
    transcription = "devis 500 euros pour le client ACME"

    with (
        patch("src.telegram.handlers.index_text") as mock_index,
        patch("src.telegram.handlers.anthropic") as mock_anthropic,
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Note : devis 500 € ACME")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        from src.telegram.handlers import process_voice_memo

        await process_voice_memo(mock_session, tenant_id, transcription)

    mock_index.assert_called_once_with(mock_session, tenant_id, transcription)


@pytest.mark.asyncio
async def test_summary_starts_with_note(mock_session, tenant_id):
    """The confirmatory summary returned should start with 'Note'."""
    with patch("src.telegram.handlers.index_text"), patch("src.telegram.handlers.anthropic") as mock_anthropic:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Note : réunion lundi à 10h")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        from src.telegram.handlers import process_voice_memo

        result = await process_voice_memo(mock_session, tenant_id, "réunion lundi à 10h avec le client")

    assert result is not None
    assert result.startswith("Note")
