# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-16

### Added

- Initial scaffold of the CLI with subcommands for clients, products, quotes, and invoices.
- `ping` command to verify credentials and show organization / bank accounts.
- Clients: list, find (fuzzy), get, create, update.
- Products: list, find, get, create, update (delete + recreate — new id), delete.
- Quotes: list, find, get, create (with per-item and global discounts), update (draft only), send via Qonto email.
- Invoices: list, find, get, create (draft or finalized), update (draft only), finalize, send via Qonto email, mark as paid, cancel.
- `quote-validate` workflow: converts a quote into a draft invoice and records the mapping in `state.json`.
- `pending-payments` report combining unpaid invoices and validated quotes not yet paid.
- Automatic PDF download for created / finalized documents, preserving the filename provided by Qonto via `Content-Disposition`.
- Claude Code skill (`.claude/skills/devis-qonto/SKILL.md`) for conversational usage.
- Anonymized example payloads in `examples/`.
