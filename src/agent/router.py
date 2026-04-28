COMPLEX_KEYWORDS = ["analyse", "synthèse", "compare", "tendance", "bilan", "récap", "optimise"]


def select_model(message: str) -> str:
    lower = message.lower()
    if any(kw in lower for kw in COMPLEX_KEYWORDS):
        return "claude-sonnet-4-6"
    return "claude-haiku-4-5-20251001"
