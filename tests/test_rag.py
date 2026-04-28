"""Tests for RAG — business memory (pgvector)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.rag.entity_detector import contains_business_entity, should_index

# ---------------------------------------------------------------------------
# entity_detector tests — no external dependencies
# ---------------------------------------------------------------------------


def test_detects_amount():
    assert contains_business_entity("Budget 5000 euros pour le projet")


def test_detects_amount_eur():
    assert contains_business_entity("Facture de 1200 EUR reçue")


def test_detects_amount_symbol():
    assert contains_business_entity("devis 500€")


def test_detects_date_slash():
    assert contains_business_entity("Livraison le 15/06")


def test_detects_date_dash():
    assert contains_business_entity("RDV le 03-07")


def test_detects_month_name():
    assert contains_business_entity("Réunion en janvier")


def test_detects_weekday():
    assert contains_business_entity("On se voit lundi")


def test_detects_keyword_client():
    assert contains_business_entity("nouveau client ACME")


def test_detects_keyword_facture():
    assert contains_business_entity("J'ai envoyé la facture")


def test_detects_keyword_devis():
    assert contains_business_entity("Le devis est prêt")


def test_no_entity():
    assert not contains_business_entity("ok merci")


def test_no_entity_empty():
    assert not contains_business_entity("")


def test_short_without_entity_not_indexed():
    assert not should_index("ok merci")


def test_short_with_entity_indexed():
    assert should_index("devis 500€")


def test_long_message_indexed():
    assert should_index("Je dois rappeler le client demain matin pour confirmer la livraison du matériel")


def test_long_message_without_entity_indexed():
    # More than 5 words → indexed regardless of entities
    assert should_index("Voici un message sans entité particulière mais long")


# ---------------------------------------------------------------------------
# embeddings — mock OpenAI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_embedding_calls_openai():
    fake_embedding = [0.1] * 1536

    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_embedding)]

    with patch("src.rag.embeddings.openai_client") as mock_client:
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        from src.rag.embeddings import generate_embedding

        result = await generate_embedding("test texte")

    assert result == fake_embedding
    mock_client.embeddings.create.assert_called_once_with(model="text-embedding-3-small", input="test texte")


# ---------------------------------------------------------------------------
# indexer — mock DB + embeddings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_index_text_adds_memory():
    fake_embedding = [0.0] * 1536
    tenant_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch("src.rag.indexer.generate_embedding", AsyncMock(return_value=fake_embedding)):
        from src.models.memory import MemoryEmbedding
        from src.rag.indexer import index_text

        await index_text(mock_session, tenant_id, "Budget 5000 euros")

    mock_session.add.assert_called_once()
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, MemoryEmbedding)
    assert added_obj.tenant_id == tenant_id
    assert added_obj.content == "Budget 5000 euros"
    assert added_obj.embedding == fake_embedding
    mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# search — mock DB + embeddings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_memory_returns_contents():
    fake_embedding = [0.1] * 1536
    tenant_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.all.return_value = [("Contenu 1",), ("Contenu 2",)]

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("src.rag.search.generate_embedding", AsyncMock(return_value=fake_embedding)):
        from src.rag.search import search_memory

        results = await search_memory(mock_session, tenant_id, "recherche test", limit=2)

    assert results == ["Contenu 1", "Contenu 2"]
    mock_session.execute.assert_called_once()


# ---------------------------------------------------------------------------
# agent tools/memory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_memo_returns_confirmation():
    tenant_id = uuid.uuid4()
    mock_session = AsyncMock()

    with patch("src.agent.tools.memory.index_text", AsyncMock()):
        from src.agent.tools.memory import save_memo

        result = await save_memo(mock_session, tenant_id, "note importante")

    assert result == "Memo sauvegardé."


@pytest.mark.asyncio
async def test_search_memo_delegates_to_search_memory():
    tenant_id = uuid.uuid4()
    mock_session = AsyncMock()
    expected = ["résultat 1", "résultat 2"]

    with patch("src.agent.tools.memory.search_memory", AsyncMock(return_value=expected)):
        from src.agent.tools.memory import search_memo

        results = await search_memo(mock_session, tenant_id, "ma recherche")

    assert results == expected
