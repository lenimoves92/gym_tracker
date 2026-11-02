# Resilience: DB connections (2026-11-02)

Context: Supabase DB restarted Mon 2026-10-26 19:10 UTC and the app hung on
every page; Render cold starts needed several attempts.

- [x] 1. `connect_timeout=10` in `get_db()` so a dead DB fails fast instead of hanging
- [x] 2. Startup survives an unreachable DB (`init_db()` failure is logged, not fatal)
- [x] 3. Every route closes its connection, even on errors (`db_cursor()` context manager)
- [x] Verify: all pages render locally against Supabase, duplicate-exercise path,
      unreachable DB → startup OK + fast failure, connections closed on exceptions
- [x] 4. gunicorn: added to requirements.txt, render.yaml startCommand updated
- [ ] Deploy: push to main, set Start Command in Render dashboard, verify
      `x-render-origin-server` header shows gunicorn instead of Werkzeug

## Review

- `database.db_cursor()` commits on success, rolls back on error, always closes.
  All routes use it; `add_equipment` now catches only `psycopg2.IntegrityError`
  (previously any error, incl. DB outages, was shown as "already exists").
- Verification (local new code, live Supabase, no data written):
  - 6 page variants render byte-identical (whitespace-normalised) to the live old code
  - Duplicate "Dip" → "already exists" flash (UNIQUE constraint)
  - 10 connections opened, 0 left open, incl. forced `DivisionByZero`
  - Non-routable DB host: app imports after ~11s with warning logged;
    request returns 500 after 10s instead of hanging
