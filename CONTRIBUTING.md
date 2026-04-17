# Contributing

Thanks for your interest. This project is small and opinionated — contributions are welcome, but please keep the scope tight.

## Before opening an issue

- Search existing issues first.
- For bugs: include the command you ran, the expected behavior, and the actual behavior (with the error message, redacted of any credentials or client data).
- For feature requests: describe the workflow you're trying to accomplish before proposing an implementation.

## Before opening a pull request

1. Open an issue first if the change is non-trivial (> a dozen lines). This avoids wasted work on something that doesn't fit the project's direction.
2. Keep changes focused: one feature or fix per PR.
3. Stick to the existing code style (ESM, no dependencies beyond Node 18+ built-ins, no TypeScript).
4. Add example payloads under `examples/` if you introduce new endpoints — always anonymized.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## What will not be accepted

- Contributions that add a runtime dependency without strong justification. Node 18+ built-ins cover everything needed.
- Contributions that log or persist credentials, client data, or invoice content outside of the documented `pdf/` and `state.json` locations.
- Contributions that expose destructive endpoints (delete client, delete quote, delete invoice) in the CLI. These are intentionally not exposed — use the Qonto web interface for these operations.
- Contributions that bypass the confirmation flows documented in the skill (`SKILL.md`). Every mutation goes through a resolve → summarize → confirm → execute cycle.

## Security

If you discover a security issue (credential leak, unsafe payload handling, etc.), do not open a public issue. Contact the maintainer via the GitHub profile instead.
