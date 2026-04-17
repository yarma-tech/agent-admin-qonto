# agent-admin-qonto

A small Node.js CLI and Claude Code skill to manage quotes, invoices, clients and products on [Qonto](https://qonto.com) through the Business API — without leaving the terminal (or a chat with Claude).

> **Not affiliated with Qonto.** See [DISCLAIMER.md](DISCLAIMER.md).

---

## What it does

- Create, update, list, search **quotes** (with per-item and global discounts)
- Create, update (drafts), finalize, list, search **invoices**
- Full CRUD on **clients** and **products** (article catalog)
- **Validate a quote** → creates a draft invoice from the quote items, tracking the link locally
- Compute the **sum of pending payments** (unpaid invoices + validated quotes not yet paid)
- **Download PDF** automatically after creation / finalization, keeping the filename Qonto assigns
- **Send by email via Qonto's infrastructure** (no SMTP needed on your side)

Everything runs locally, credentials stay in `.env`, PDFs are stored under `pdf/` (gitignored).

---

## Why

I want to describe an invoice in natural language ("1500€ HT for ACME, consulting for March, 8.5% VAT") and have it created properly in Qonto, with a clean audit trail and a PDF on my disk. The CLI does the boring parts; the skill drives it from a conversation.

---

## Requirements

- Node.js ≥ 18 (native `fetch` is used — no dependency needed)
- A Qonto Business account with API access
- An API key with the following scopes:
  - `organization.read`
  - `client.read`, `client.write`
  - `product.read`, `product.write`
  - `client_invoices.read`, `client_invoice.write`

Generate the key in Qonto → Settings → Integrations.

---

## Install

```bash
git clone https://github.com/yarma-tech/agent-admin-qonto.git
cd agent-admin-qonto
cp .env.example .env
# edit .env and fill in QONTO_ORGANIZATION_SLUG and QONTO_SECRET_KEY
```

No `npm install` needed — the project has no runtime dependencies.

---

## Quick check

```bash
node src/cli.js ping
```

Expected output: JSON with your organization name and bank accounts.

---

## CLI usage

All commands emit JSON on stdout. Errors go to stderr with a non-zero exit code.

### Base

```bash
node src/cli.js ping
node src/cli.js help
```

### Clients

```bash
node src/cli.js client-list
node src/cli.js client-find "ACME"
node src/cli.js client-get --id <uuid>
node src/cli.js client-create --json examples/client-create.json
node src/cli.js client-update --id <uuid> --json patch.json
```

### Products

```bash
node src/cli.js product-list
node src/cli.js product-find "consulting"
node src/cli.js product-create --json examples/product-create.json
# update = delete + recreate (new id)
node src/cli.js product-update --id <uuid> --json new-payload.json
node src/cli.js product-delete --id <uuid>
```

### Quotes

```bash
node src/cli.js quote-list --client-id <uuid> --from 2026-01-01 --to 2026-04-30
node src/cli.js quote-find "DEV-2026-042"
node src/cli.js quote-create --json examples/quote-simple.json
node src/cli.js quote-create --json examples/quote-with-discount.json
node src/cli.js quote-update --id <uuid> --json patch.json       # drafts only
node src/cli.js quote-send --id <uuid> --json send-payload.json
node src/cli.js quote-validate --id <uuid>                        # creates draft invoice
```

### Invoices

```bash
node src/cli.js invoice-list --status unpaid
node src/cli.js invoice-list --client-id <uuid>
node src/cli.js invoice-find "FAC-2026-012"
node src/cli.js invoice-create --json examples/invoice-simple.json
node src/cli.js invoice-create --json examples/invoice-simple.json --finalize
node src/cli.js invoice-update --id <uuid> --json patch.json     # drafts only
node src/cli.js invoice-finalize --id <uuid>
node src/cli.js invoice-send --id <uuid> --json send-payload.json
node src/cli.js invoice-mark-paid --id <uuid> --paid-at 2026-04-16
node src/cli.js invoice-cancel --id <uuid>
```

### Reports

```bash
node src/cli.js pending-payments
node src/cli.js pending-payments --detailed
```

---

## Discounts

Both quotes and invoices support per-item and global discounts using the same shape:

```json
{
  "type": "percentage",
  "value": "10"
}
```

`type` is `"percentage"` or `"amount"`. `value` is always a string. You can combine per-item discounts with a global discount. The CLI rejects percentages above 100 and negative values.

See [examples/quote-with-discount.json](examples/quote-with-discount.json).

---

## Email sending

Quotes and invoices are sent via Qonto's own email infrastructure — **not from your personal email or SMTP**. No mail server configuration needed.

`send-payload.json`:

```json
{
  "send_to": ["billing@client.example"],
  "email_title": "Invoice FAC-2026-012",
  "email_body": "Optional message.",
  "copy_to_self": true
}
```

`copy_to_self` (default true) sends a copy to the email address associated with your Qonto user. Qonto's API does not support CC or BCC.

---

## Claude Code skill

The project ships a skill at `.claude/skills/devis-qonto/SKILL.md` that drives this CLI conversationally. Once the project is opened in Claude Code, invoke it with phrases like:

- "devis 1500€ pour ACME, prestation mars"
- "valide le devis DEV-2026-042"
- "factures impayées de ACME"
- "combien de paiements en attente"

The skill always resolves references (client, document), shows a summary, and asks for confirmation before any POST. It refuses to modify finalized invoices and warns before any product update (which creates a new id).

---

## State

`state.json` (gitignored) stores the mapping between validated quotes and the invoices they produced:

```json
{
  "validated_quotes": {
    "<quote_id>": {
      "quote_number": "DEV-2026-042",
      "validated_at": "2026-04-16T10:00:00Z",
      "invoice_id": "<invoice_id>",
      "invoice_number": "FAC-2026-012"
    }
  }
}
```

Used by `pending-payments` to exclude already-paid conversions. If lost, reports degrade gracefully (may overestimate) but nothing breaks on Qonto's side.

---

## Design notes

- Node.js built-ins only (`fetch`, `fs/promises`, `path`). Zero runtime dependencies.
- ESM everywhere.
- Credentials loaded from `.env` at each CLI invocation. No config file, no global state.
- PDFs are downloaded with `Content-Disposition` filenames preserved. On filename collision, a suffix `_(2)`, `_(3)`... is added.
- All monetary values are passed as strings (`"1500.00"`) to avoid floating-point issues.

---

## Roadmap

Phase 2 (not yet implemented): a Telegram bot wrapper in `telegram/` that accepts voice and text messages, transcribes voice through Whisper, and routes to the same CLI commands. Same confirmation flow as the Claude Code skill.

---

## Section FR — résumé rapide

Outil pour gérer devis, factures, clients et articles Qonto en ligne de commande ou via Claude Code. TVA 8.5% par défaut (DOM), validité 30 jours, numérotation auto Qonto. Aucune dépendance npm, credentials dans `.env` (gitignored), PDF stockés localement avec le nom original Qonto. L'envoi email passe par l'infrastructure Qonto (pas de SMTP à configurer). Skill Claude en français dans `.claude/skills/devis-qonto/SKILL.md`.

---

## License

[MIT](LICENSE)
