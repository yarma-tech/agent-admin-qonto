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

## Speakinvoices (by Maiya Inc.) — MVP in development

This codebase is also the engine for **Speakinvoices**, a commercial SaaS product by **Maiya Inc.** targeting freelancers and small businesses who want to send quotes and invoices in **2 minutes by voice** — versus the typical **24-48h** workflow today. A quote sent within the hour has 2-3x more chances of being signed than one sent 48h later: that's the differentiator.

The product is built as:

- **Web interface** (Next.js, hosted by Maiya Inc.) — MVP first
- **Voice-first UX** in the browser via the native Web Speech API + LLM agent (Vercel AI SDK)
- **Multi-provider** invoicing tools: **Qonto** (France) and **QuickBooks Online** (US/CA/UK/AU) at MVP, with Shine, Pennylane, and Xero in later phases
- **Native iOS app** in a later phase (post-MVP web validation)

Hosting model: **fully hosted by Maiya Inc.** (SaaS), not self-hosted. The customer connects their Qonto or QuickBooks account via OAuth and uses Speakinvoices through the browser — no install, no infrastructure to manage.

Status: **MVP demo sprint in progress** — a working web demo connected to QuickBooks Online sandbox is targeted for end of April 2026. Validation interviews with target ICP (videographers / motion designers FR) run in parallel: see [docs/validation/](docs/validation/). Full strategic plan: [`.claude/plans/voici-des-fonctionnalit-s-delegated-rossum.md`](.claude/plans/voici-des-fonctionnalit-s-delegated-rossum.md).

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
node src/cli.js pdf-dir                                    # show current PDF destination
node src/cli.js pdf-dir --set "/path/to/your/pdf/folder"   # set PDF destination (quotes required for paths with spaces)
```

### PDF destination

Generated PDFs (quotes + finalized invoices) are saved to the folder configured in `state.json` under `pdf_destination`. If unset, PDFs default to the project's `pdf/` folder.

- First-time setup: `node src/cli.js pdf-dir --set "/absolute/path"`
- Inspect current value: `node src/cli.js pdf-dir`
- The skill confirms the destination before every create / finalize and lets you change it on the fly.

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
  "value": "0.10"
}
```

`type` is `"percentage"` or `"amount"`. `value` is always a string. For `percentage`, Qonto expects a **decimal fraction between 0 and 1** — `"0.10"` means 10%, `"0.20"` means 20%. Sending `"10"` or `"20"` is rejected by both the CLI and the Qonto API. For `amount`, it's a normal money string like `"50.00"`. You can combine per-item discounts with a global discount. The CLI rejects percentage values above 1 and negative values.

### VAT rate format

Qonto expects VAT rates as **decimal fractions** passed as strings: `"0.085"` means 8.5%, `"0.2"` means 20%, `"0"` means exempt. This applies everywhere the API takes a `vat_rate` field (products, quote items, invoice items).

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

## Known limitations

### Product individual endpoints return 404

`GET /v2/products/{id}` and `DELETE /v2/products/{id}` return `404 Not Found` on our test Qonto Business account, even when the product is clearly present in `GET /v2/products` (list). This affects the `product-update` and `product-delete` CLI commands — they will fail with a clear error message pointing to the web UI.

- **Status** as of 2026-04-16: reproducible with both UI-created and API-created products, across four URL variants (`/v2/products/{id}`, `/v2/products/{id}/`, `/v2/catalog/products/{id}`, `/v2/products?id=…`). The endpoint documentation explicitly lists `SecretKey` as an accepted auth method, so this is not a scope/auth issue.
- **Workaround**: manage product updates and deletions via the Qonto web interface (<https://app.qonto.com> → Billing → Products). `product-list`, `product-find` and `product-create` continue to work normally through the API.

If you can reproduce this with your own Qonto account, consider opening a support ticket with Qonto.

### No CC/BCC on email sending

Qonto's `send-a-quote` and `send-a-client-invoice` endpoints only accept `send_to` (array) and `copy_to_self` (boolean). There is no `cc` or `bcc` field. For multi-recipient sends, list all addresses in `send_to`.

---

## Roadmap

This engine (Qonto CLI + skill) is the foundation for **Speakinvoices** by Maiya Inc. Full strategic plan: [`.claude/plans/voici-des-fonctionnalit-s-delegated-rossum.md`](.claude/plans/voici-des-fonctionnalit-s-delegated-rossum.md).

### 🔥 Sprint MVP demo — QuickBooks (5 days, in progress)

A working web demo that creates a real invoice in QuickBooks Online (sandbox) by voice command. Stack: Next.js 15 + Vercel Pro + Supabase + Vercel AI SDK + OpenAI GPT-4o-mini + Web Speech API + Intuit OAuth 2.0. Day-by-day plan in the strategic plan file.

### Phase 1 — Post-demo polish + Qonto integration (weeks 2-4)

- Polish based on demo feedback
- Add Qonto provider (reuses `src/qonto.js` wrapped in TypeScript)
- Multi-tenant auth (Clerk) + onboarding flow
- Stripe billing (subscription €12-19/month, TBD)
- Private beta with 5-10 freelancers (recruited via [docs/validation/](docs/validation/))

### Phase 2 — Brief PDF + new providers + iOS (months 2-4)

- **Brief PDF → invoice**: agent ingests a client brief and proposes a draft (reuses ideas from this README's original "brief-to-quote" plan)
- **More providers**: Shine (FR), Pennylane (compta, complementary), Xero (UK/AU)
- **Native iOS app** (SwiftUI) — pushed back from initial plan due to web MVP urgency

### Phase 3 — RAG + public launch (months 4-6)

- RAG over invoice/quote history (premium tier feature)
- Public marketing launch
- Metier packs: videographers, motion designers, consultants, BTP artisans

### Phase superseded — original Phase 2 plans

The original roadmap (Telegram long-poll bot, standalone MCP server, brief-to-quote as a CLI feature) is folded into the Speakinvoices phases above:
- Telegram bot → could resurface as alternate channel in Phase 2+ if demand emerges; not on the critical path
- MCP server → could resurface for non-Speakinvoices users; not on the critical path
- Brief-to-quote → Phase 2

---

## Section FR — résumé rapide

Outil pour gérer devis, factures, clients et articles Qonto en ligne de commande ou via Claude Code. TVA 8.5% par défaut (DOM), validité 30 jours, numérotation auto Qonto. Aucune dépendance npm, credentials dans `.env` (gitignored), PDF stockés localement avec le nom original Qonto. L'envoi email passe par l'infrastructure Qonto (pas de SMTP à configurer). Skill Claude en français dans `.claude/skills/devis-qonto/SKILL.md`.

---

## License

[MIT](LICENSE)
