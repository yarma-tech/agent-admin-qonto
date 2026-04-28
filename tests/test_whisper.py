from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.tools.transcribe import transcribe_voice


@pytest.mark.asyncio
async def test_transcribe_returns_text() -> None:
    mock_response = MagicMock()
    mock_response.text = "Bonjour, crée un devis pour ACME"
    with patch("src.agent.tools.transcribe.openai_client") as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        result = await transcribe_voice(b"fake-audio-bytes", "ogg")
        assert result == "Bonjour, crée un devis pour ACME"


@pytest.mark.asyncio
async def test_transcribe_sends_correct_params() -> None:
    mock_response = MagicMock()
    mock_response.text = "test"
    with patch("src.agent.tools.transcribe.openai_client") as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        await transcribe_voice(b"data", "mp3")
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-1"
        assert call_kwargs["language"] == "fr"
        assert call_kwargs["file"].name == "voice.mp3"
