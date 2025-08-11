# Changelog

## 1.1.0 — 2025-08-10

- Persist SQLite on Render via mounted disk and `DB_PATH`.
- One-time seed of persistent DB from bundled `trials.db`.
- Add admin diagnostics JSON/UI and DB health endpoints.
- Admin-run and cron-protected endpoints to expire trials.
- Switch to `gunicorn` for production serving (Blueprint/Procfile).
- Add Render Blueprint env vars and disk; docs for deployment and cron.
- Minor: production-aware debug flags; dashboard links; tests still passing.

## 1.0.0 — Initial
- Initial public version.
