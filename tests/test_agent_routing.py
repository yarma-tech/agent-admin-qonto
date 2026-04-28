from src.agent.router import select_model


def test_simple_query_uses_haiku():
    assert select_model("Crée un devis pour ACME") == "claude-haiku-4-5-20251001"


def test_complex_query_uses_sonnet():
    assert select_model("Analyse mes dépenses des 3 derniers mois") == "claude-sonnet-4-6"


def test_empty_message_uses_haiku():
    assert select_model("") == "claude-haiku-4-5-20251001"
