# Agent Qonto — Architecture & Decisions

## Produit

Agent IA Telegram pour freelances Qonto. Gere devis, factures et memoire business par la voix et le texte. 24/7.

**Cible** : Freelances francais non-tech utilisant Qonto.

## Architecture

```
TON VPS HOSTINGER (8GB RAM, 2 vCPU, 100GB)
+-- Docker Compose
|   +-- FastAPI (backend principal)
|   |   +-- Bot Telegram (webhook, 1 bot pour tous les clients)
|   |   +-- Agent SDK Claude (Haiku 90% / Sonnet 10%)
|   |   +-- Whisper API OpenAI (transcription vocale)
|   |   +-- RAG engine (memoire business par client)
|   |   +-- Stripe (billing + webhooks)
|   |   +-- Auth (Telegram user_id, pas de compte separe)
|   +-- PostgreSQL + pgvector (DB multi-tenant)
|   +-- Redis (file d'attente)
|   +-- Landing page statique (one-pager)

RAILWAY CLIENT (1 par client, ~5$/mois)
+-- Proxy Qonto (FastAPI leger)
    +-- Cle API Qonto (jamais chez nous)
    +-- Execute les ordres du backend central
    +-- Securise par token partage
```

## Communication Cloud <-> Railway Client

- WebSocket entre le backend central et chaque proxy Railway
- Token partage genere a l'onboarding, stocke dans les variables d'env Railway du client
- Health check toutes les 6h, notification client apres 3 echecs consecutifs

## Agent SDK Claude

- **Instanciation** : stateless, 1 agent par requete, historique en DB
- **Contexte par requete** : 10 derniers messages + top 5 resultats RAG
- **Confirmation obligatoire** avant chaque ecriture Qonto (meme comportement que le skill existant)
- **Routage intelligent** :
  - Haiku/GPT-4o-mini (~90%) : requetes simples (creer devis, lister factures)
  - Sonnet/GPT-4o (~10%) : analyse RAG complexe, synthese financiere

### Tools de l'agent

| Tool | Description | Direction |
|---|---|---|
| transcribe_voice | Whisper API (vocal -> texte) | Interne |
| search_memory | Recherche semantique RAG (pgvector) | Interne |
| save_memo | Indexe un memo dans le RAG | Interne |
| qonto_create_quote | Creer un devis | -> Proxy Railway |
| qonto_update_quote | Modifier un devis (brouillon) | -> Proxy Railway |
| qonto_send_quote | Envoyer un devis par email | -> Proxy Railway |
| qonto_validate_quote | Valider un devis -> facture | -> Proxy Railway |
| qonto_create_invoice | Creer une facture | -> Proxy Railway |
| qonto_finalize_invoice | Finaliser une facture | -> Proxy Railway |
| qonto_send_invoice | Envoyer une facture par email | -> Proxy Railway |
| qonto_list_invoices | Lister les factures | -> Proxy Railway |
| qonto_list_quotes | Lister les devis | -> Proxy Railway |
| qonto_pending_payments | Paiements en attente | -> Proxy Railway |
| qonto_client_find | Chercher un client | -> Proxy Railway |
| qonto_client_create | Creer un client | -> Proxy Railway |
| qonto_product_find | Chercher un article | -> Proxy Railway |

## RAG — Memoire Business

- **Alimentation** : memos vocaux Telegram + conversations indexees automatiquement
- **Filtre** : messages > 5 mots ou contenant une entite business (client, montant, date, projet)
- **Stockage** : PostgreSQL + pgvector sur le VPS
- **Par client** : isolation totale (tenant_id sur chaque embedding)

### Comportement memo vocal

- **Par defaut** : resume court confirmatif ("Note : RDV KADO / Polobi — 3j tournage + 2j montage, budget 5K, livraison fin mai. Je m'en souviendrai.")
- **Si ambiguite critique** : resume + questions ("...budget 5K TTC ou HT ?")

## Business Model

### Pricing

| Palier | Prix affiche | Ton revenu | Inclus |
|---|---|---|---|
| Solo | 9.90 EUR/mois | ~5 EUR | 50 ecritures Qonto/mois + RAG standard |
| Pro | 9.90 EUR/mois | ~7 EUR | Ecritures illimitees + RAG etendu |

- **9.90 EUR/mois tout inclus** (ton service + Railway client)
- **LLM + Whisper** : paye par toi, absorbe dans la marge
- **Memos vocaux** : illimites sur tous les paliers
- **Actions = ecritures Qonto uniquement** (lectures, RAG, conversation = illimites)

### Definition d'une action (ecriture Qonto)

- Creer un devis
- Creer une facture
- Envoyer un email (devis/facture)
- Modifier un devis/facture
- Valider un devis -> facture

### Cout reel par client/mois

| Poste | Cout |
|---|---|
| Railway (proxy Qonto) | ~3-5 USD |
| LLM (routage intelligent) | ~1-1.50 EUR |
| Whisper API | ~0.50 EUR |
| Infra VPS (mutualise) | ~0.20 EUR |
| **Total** | **~5-7 EUR** |

## Securite

- **Cle API Qonto** : jamais chez nous, reste sur le Railway du client
- **Token partage** : securise la communication cloud <-> proxy Railway
- **Donnees RAG** : chiffrees, isolees par tenant
- **Retention apres resiliation** : 30 jours puis suppression, export possible a tout moment

## Onboarding Client

```
1. Landing page -> CTA "Demarrer sur Telegram" -> t.me/[Bot]
2. /start -> lien Stripe Checkout (user_id Telegram en metadata)
3. Webhook Stripe confirme -> bot guide l'onboarding
4. Tuto video Railway : creer compte, one-click deploy, coller cle Qonto
5. Option : screen share payant pour setup assiste
6. Bot ping le proxy Railway -> "Connecte ! Envoie-moi ton premier vocal."
```

## Monitoring & Resilience

- **Health check** : ping proxy Railway toutes les 6h
- **3 echecs consecutifs** : notification Telegram au client
- **7 jours down** : pause auto abonnement Stripe
- **Resiliation Stripe** : webhook -> bot notifie de supprimer Railway -> acces coupe
- **Resiliation Railway sans prevenir** : detecte par health check -> pause Stripe auto

## Scope V1

- Creer / modifier / envoyer devis et factures (voix ou texte)
- Memo vocal -> memoire business RAG
- Lister transactions, factures impayees, paiements en attente
- CRUD clients et articles
- Suivi conso tokens (dans Telegram)
- Landing page one-pager

## Scope V2

- Dashboard web (suivi devis/factures, analyse perte/benefice, conso tokens)
- Canal WhatsApp (WhatsApp Business API)
- Export donnees
- Whisper self-hosted (quand > 200 clients)

## Stack Technique

| Composant | Technologie |
|---|---|
| Backend principal | Python / FastAPI |
| Agent IA | Claude Agent SDK (Haiku + Sonnet) |
| Transcription vocale | Whisper API (OpenAI) |
| Base de donnees | PostgreSQL + pgvector |
| File d'attente | Redis |
| Proxy Qonto (client) | Python / FastAPI (leger) |
| Landing page | HTML/CSS/JS statique (ou React) |
| Paiement | Stripe |
| Hebergement central | VPS Hostinger (Docker Compose) |
| Hebergement client | Railway (one-click deploy) |
| Bot Telegram | python-telegram-bot / webhook |

## Skill Existant (Reference)

Le skill Claude Code dans `/Users/YarmaVideos/Developer/divers/Devis-Qonto/` sert de **specification fonctionnelle** pour le module Qonto. Il definit :
- Tous les workflows (creation devis, factures, validation, envoi email)
- Les guardrails (confirmation avant POST, refus modification doc finalise)
- Les payloads JSON attendus par l'API Qonto
- La gestion des erreurs

Ce skill Node.js local sera reecrit en Python/FastAPI pour le proxy Railway.
