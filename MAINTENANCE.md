# Carbon Intelligence App – Operations & Maintenance Guide

This guide summarizes the routine actions needed to keep `carbon-intelligence-ai.onrender.com` healthy. (Created automatically – adjust as you like.)

---
## 1. Daily / Routine Checks
- Visit `/health` and `/health/db` – confirm `status=online`, trial counts > 0.
- Glance at Render Logs for new `ERROR`, `⚠️`, or `[DB]` warnings.
- Export a dated backup: visit `/admin/export-csv-full` (logged in) and save as `backups/trials_YYYYMMDD.csv` locally.

## 2. Before Any Deploy / Code Change
1. Take a fresh full CSV backup (`/admin/export-csv-full`).
2. Commit & push code.
3. After deploy, verify logs: seeded trial or existing data (on free tier a reseed is expected after rebuild).
4. Re‑test `/validate_trial` and a sample `/search`.

## 3. Environment Variables (Render → Environment)
Keep these defined as needed:
| Key | Purpose | Notes |
|-----|---------|-------|
| `DB_PATH` | Preferred persistent path `/var/data/trials.db` | On free tier falls back automatically. Optional to remove. |
| `SUPPRESS_PERSIST_WARN` | Set `1` to silence non‑persistent warning | Cosmetic. |
| `GOOGLE_API_KEY` / `GOOGLE_CSE_ID` | Google Custom Search | Optional if not using. |
| `SERPER_API_KEY` | Serper engine | Optional. |
| `TAVILY_API_KEY` | Tavily engine | Optional. |
| `SEARCH_USE_DDG` | `true/false` include DuckDuckGo | Defaults to false. |
| `SECRET_KEY` | Flask session secret | Rotate if leaked. |
| `CRON_SECRET` | Auth token for `/cron/run-expire` | Only if scheduling expiration. |
| `SEED_TRIAL_KEY`, `SEED_TRIAL_EMAIL`, `SEED_TRIAL_MAX_QUERIES` | Seed customization | Only used when DB empty. |
| `ALLOW_DB_FALLBACK` | Allow fallback if `/var/data` unwritable | Defaults enabled. Set `0` to force failure. |

## 4. Trial Management
- Register: `/register-trial` UI or POST `/api/register-trial`.
- Validate: POST `/validate_trial`.
- Usage & status: `/admin/dashboard` or `/admin/painel` (HTML) and `/admin/trials` (JSON).
- Force expiration update: `/admin/run-expire` (button) or POST `/cron/run-expire` with header `X-CRON-SECRET`.

## 5. Backups (Free Tier Strategy)
Because the DB file is not on a persistent disk, **data may reset on new deploys**:
- Always back up with `/admin/export-csv-full` before deployment.
- Keep multiple dated CSVs (do not overwrite).
- A future import endpoint can restore these exactly; CSV is already lossless (contains all fields).

## 6. Restore (Manual for Now)
If data resets:
1. Use default seeded trial (e.g. `CARBON-DEMO123456`) immediately.
2. Recreate critical trials manually via the registration form **or** (later) use an import script reading your full CSV backup.

## 7. Upgrading to Persistent Disk (Render Starter Plan)
1. Upgrade plan → Add Disk with Mount Path `/var/data`.
2. Ensure `DB_PATH=/var/data/trials.db` and remove (or keep) `SUPPRESS_PERSIST_WARN`.
3. Deploy and confirm `/health/db` shows path under `/var/data` (warning disappears).
4. Import historical CSV once an import tool exists (or write a one-off script).
5. Begin periodic raw file backups (`/var/data/trials.db`) using shell or snapshot plus continued CSV backups.

## 8. Search Subsystem
- Parallel engines: Google, Serper, Tavily (+ optional DDG) with graceful fallback.
- Disable an engine by removing its API key or toggling `SEARCH_USE_DDG`.
- Logs prefix: `[SEARCH]` for query diagnostic lines.

## 9. Security & Secrets
- Keep `SECRET_KEY` and external API keys private; rotate if exposed.
- Protect admin routes with the simple session login (consider hardening later: stronger creds or OAuth).
- Protect cron route with `CRON_SECRET` header.

## 10. Admin Routes Summary
| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/admin/dashboard` | Dashboard (inline HTML) | Yes |
| `/admin/painel` | Alternative dashboard template (PT-BR) | Yes |
| `/admin/trials` | JSON list of trials | Yes |
| `/admin/export-csv` | Basic CSV export | Yes |
| `/admin/export-csv-full` | Lossless CSV export (backup) | Yes |
| `/admin/run-expire` | Manual expiration update | Yes |
| `/admin/diagnostics` | DB & disk diagnostics JSON | Yes |
| `/admin/diagnostics-view` | Diagnostics HTML | Yes |

## 11. Scheduled Expiration (Optional)
Until a Render cron job or external scheduler:
- Use an external service (GitHub Actions curl, Zapier, etc.) to POST `/cron/run-expire` with header `X-CRON-SECRET: <value>` daily.

## 12. Troubleshooting Quick Reference
| Symptom | Likely Cause | Action |
|--------|--------------|--------|
| `sqlite3.OperationalError: unable to open database file` | Unwritable `/var/data` on free plan | Allow fallback or remove `DB_PATH` or upgrade + add disk. |
| `Trial key inválido` after deploy | DB reseeded (fresh) | Recreate trials or restore from CSV after import tool exists. |
| `[WARN] DB path ... not on /var/data` | Running without persistent disk | Accept (free) or upgrade; set `SUPPRESS_PERSIST_WARN=1` to silence. |
| Missing search results | API key quota or engine error | Check logs for each engine; temporarily disable failing one. |
| Expired trials not updating | Cron not run | Use `/admin/run-expire` or schedule cron POST. |

## 13. Future Enhancements (Optional)
- Merge `/admin/painel` and `/admin/dashboard` into one consistent page.
- Add `/admin/import-csv` endpoint for one-click restore.
- Add UI banner when running in non-persistent fallback mode.
- Implement stronger auth (hashed password env var, etc.).

## 14. Minimal Weekly Routine
1. Export full CSV backup.
2. Review logs for new warnings.
3. Check trial usage counts and expiration.
4. Confirm search engines still returning results.
5. (If persistent disk) copy or snapshot `trials.db` occasionally.

---
**Quick Command (Local Test)**
Run locally (example):
```
python app.py
```
Then open http://localhost:5000/health

---
Questions or need new features? Add an issue / request and extend this guide.
