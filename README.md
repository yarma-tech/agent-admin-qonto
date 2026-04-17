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

### Phase 2 — Telegram agent

A Telegram bot wrapper in `telegram/` that accepts voice and text messages, transcribes voice through Whisper, and routes to the same CLI commands. Same confirmation flow as the Claude Code skill.

### Phase 2 — MCP server (expose write operations over Model Context Protocol)

Qonto ships an [official MCP server](https://github.com/qonto/qonto-mcp-server) that covers **read** operations (transactions, invoices list, statements, transfers). It does not expose **write** operations for quotes, invoices, products, or email sending.

This project already implements those write operations. Exposing them through MCP would let any MCP client (Claude Desktop, Cursor, Zed, custom agents) call them without needing a project-local skill. The two MCP servers co-exist : the official one for reads, this one for writes.

**Scope**:
- Wrap the existing CLI commands as MCP tools using [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk) (Node.js, stays consistent with the current stack)
- Expose, at minimum: `quote_create`, `quote_update`, `quote_send`, `quote_validate`, `invoice_create`, `invoice_update`, `invoice_finalize`, `invoice_send`, `invoice_mark_paid`, `invoice_cancel`, `client_create`, `client_update`, `product_create`, `pending_payments`
- Keep read-only mirrors of list/find commands for convenience, even if they overlap with the official server
- Package as Docker image (mirroring the official server's distribution model) and publish to `ghcr.io/yarma-tech/agent-admin-qonto`
- Same credential model (`.env` passed as env vars to the container)
- Preserve the confirmation-based safety flow: the MCP tool returns a "preview" structured response that the client must confirm before a second "execute" call — since MCP clients can auto-approve tools, this two-step pattern is the server-side guardrail equivalent of the skill's resolve → summarize → confirm loop

**Migration path**: the Claude Code skill at `.claude/skills/devis-qonto/SKILL.md` stays. Users on Claude Code can keep the skill (FR conversation) or switch to the MCP server (works from any client). The CLI stays as the execution backbone for both.

**Open question**: is the project better published as two separate entry points (CLI + MCP server) or a single MCP server with an optional `--cli` mode? Decide at implementation time.

### Phase 2 — Brief-to-quote generation with verification

Take a client brief (PDF, email body, meeting notes, plain text) as input and generate a matching quote draft, then run a verification pass that compares the draft back against the brief to surface any discrepancies before the user validates.

**Flow sketch**:
1. User provides a brief — path to a file, pasted text, or a Telegram attachment.
2. The agent extracts from the brief:
   - Deliverables (what's being produced)
   - Timeline / dates
   - Scope constraints and explicit exclusions
   - Any budget or rate constraint the client mentioned
   - Client identity, project name
3. The agent maps each deliverable to a catalog article via `product-find`. Falls back to ad-hoc items with a warning if no match.
4. The agent drafts a quote payload (uses catalog descriptions by default, applies existing VAT and discount rules).
5. **Verification pass** — a distinct step that compares the drafted quote back to the original brief. Flags, at minimum:
   - Deliverables in the brief absent from the quote
   - Quote items not mentioned in the brief
   - Quantity mismatches (brief says "a week of editing", quote has 2 days)
   - Timeline mismatches (brief deadline vs quote expiry)
   - Budget mismatch (brief says "max 5k", quote totals 7k)
   - Catalog matches with low confidence (agent guessed)
6. Present the draft + verification report to the user. The user either validates (→ `quote-create`), adjusts specific items, or requests a re-run with clarifications.

**Open questions to resolve at implementation time**:
- Does "corresponds to reality" mean *corresponds to the brief* (scope), *corresponds to team capacity* (can we deliver on this timeline?), or *corresponds to historical pricing* (have we done similar at this rate)? Likely the first — to confirm.
- Should verification use a separate agent/LLM pass to reduce confirmation bias, or is a single-agent structured checklist enough?
- Batch mode (process multiple briefs in a folder) — yes/no?

**Not in scope for this feature**:
- Automated quote signing by the client (Qonto handles this through its portal)
- Contract generation — this is quoting only

---

## Section FR — résumé rapide

Outil pour gérer devis, factures, clients et articles Qonto en ligne de commande ou via Claude Code. TVA 8.5% par défaut (DOM), validité 30 jours, numérotation auto Qonto. Aucune dépendance npm, credentials dans `.env` (gitignored), PDF stockés localement avec le nom original Qonto. L'envoi email passe par l'infrastructure Qonto (pas de SMTP à configurer). Skill Claude en français dans `.claude/skills/devis-qonto/SKILL.md`.

---

## License

[MIT](LICENSE)
