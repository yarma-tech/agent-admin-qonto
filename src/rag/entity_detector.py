"""Detect business entities in French text to decide whether to index a message."""

import re

AMOUNT_PATTERN = re.compile(r"\d+[\s.,]?\d*\s*(?:euros?|EUR|€|k)", re.IGNORECASE)
DATE_PATTERN = re.compile(
    r"\d{1,2}[/\-.]\d{1,2}"
    r"|\b(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre"
    r"|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b",
    re.IGNORECASE,
)
CLIENT_KEYWORDS = [
    "client",
    "projet",
    "contrat",
    "devis",
    "facture",
    "livraison",
    "réunion",
    "rdv",
]


def contains_business_entity(text: str) -> bool:
    """Return True if *text* contains at least one recognisable business entity."""
    if AMOUNT_PATTERN.search(text):
        return True
    if DATE_PATTERN.search(text):
        return True
    return any(kw in text.lower() for kw in CLIENT_KEYWORDS)


def should_index(text: str) -> bool:
    """Return True if *text* should be stored in the vector memory."""
    if len(text.split()) > 5:
        return True
    return contains_business_entity(text)
