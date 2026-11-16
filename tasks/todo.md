# Workout-type classification (2026-11-16)

- [x] Read matrix (`uebungsmatrix_gym-tracker.xlsx`): 36 rows, columns Quick/Regular/Extended/Bonus,
      exactly one "x" per row, no duplicates
- [x] Single source `exercise_types.json` (name → Q/R/E/B) + `workout_types.py` loader;
      `tools/import_exercise_types.py` regenerates the JSON from the Excel
- [x] Log dropdown shows "Name (Q)" via `with_type` filter — display only
- [x] Verify: option values still equipment ids, suffix nowhere else, DB names unchanged,
      earlier checks (PRs, ticks, overview) still pass

## Review

- Counts: Q 6 · R 9 · E 8 · B 13 (36)
- Name mismatch: Excel "Pull Up / Chin Up" vs app "Pull-Up / Chin-Up" → mapped via
  `NAME_ALIASES` in the importer (confirmed by user), so re-imports keep it
- Excel autocorrected the headers "(R)" → "®" and "(E)" → "€"; importer matches header words
- Custom exercises added later via Equipment have no type until added to the matrix

# Session ticks, 3-date chart, PRs (2026-11-16)

- [x] 0. Berlin time: `tzdata` in requirements, `local_now()` helper; new sets stamped in Europe/Berlin
- [x] 1. ✓ prefix in exercise dropdowns (Log Set + Overview) for exercises with a set logged today (Berlin day)
- [x] 2. Overview chart: last 3 session dates instead of 6
- [x] 3. Overview: PR card for selected exercise (Weight / Reps / Date), styled like session cards
      Ranking: heaviest weight (lbs→kg) > most reps > most recent
- [x] 4. New "PRs" page (`/records`): table of all exercises with logged sets, same ranking
- [x] Verify: pages render against Supabase, PR ranking incl. ties checked against raw data,
      ticks match today's sets, phone-width screenshots
- [x] 2b. Chart labels: font shrinks to fit the bar slot on narrow screens; width reserve
      for the unit fixed ('100kg' -> 'lbs') — 3 bars still overlapped at 375px before this
- [x] 2c. Dropped the "s1:/s2:" label prefix (phone + desktop) — labels ~14px at 360px instead of ~11px;
      tooltip still names the set
- [x] 5. Desktop Overview fits one screen without scrolling: Log button on the selector row,
      PR card under the chart (CSS grid; phone order unchanged), chart height follows the
      window height, tighter card rows on desktop. Measured page height == window height at
      1500×668, 1366×650, 1280×720, 1024×700, 1920×950, 1500×620 incl. 4- and 6-set sessions
- [x] 6. Overview relayout (one CSS grid, `.ov-page`):
      Phone: title + Log / selector / chart / PR / sessions; compact rows, PR + session tables
      share fixed column widths (# | Reps | Weight | RPE/Date), Previous session hides the
      repeated header, Overview-only smaller page margins (`container_spacing` block in base).
      Fits one screen at 390×700, 360×740, 412×800 (3-set sessions); 375×667 and 4-set
      sessions still scroll ~20–30px. Dropdown no longer overflows at 360px.
      Desktop: selector · PR · Log in one row; still no scroll at all sizes from item 5
- [x] 7. Phone nav (<576px): brand line + all 5 buttons on one line below (labels same size,
      tighter padding/gaps, brand 1.1rem); "Log Set" → "Log". Nav 118px → 72px on every page.
      Overview now fits at 320×700, 360×740, 375×667, 390×700, 412×800 incl. 4-set sessions

## Review

- Berlin time via `zoneinfo` + `tzdata` (Windows has no tz database). New sets are stamped
  in Berlin time; existing rows were stamped in UTC on Render and are left untouched.
- `PR_ORDER` (app.py) is shared by the Overview PR card and `/records`.
- Verification (local, live Supabase, read-only):
  - All 25 PRs on `/records` match an independent Python computation; 2 exercises have exact
    weight+reps ties at the PR and the most recent set wins in both
  - ✓ ticks on Log Set + Overview match exactly the 5 exercises with sets dated today
  - Overview renders for all 36 exercises, chart ≤ 3 dates, "no data" PR card when empty
  - All 5 pages 200; screenshots at 360/375px and 1000px: no overlap, no horizontal scroll

# Resilience: DB connections (2026-11-02)

Context: Supabase DB restarted Mon 2026-10-26 19:10 UTC and the app hung on
every page; Render cold starts needed several attempts.

- [x] 1. `connect_timeout=10` in `get_db()` so a dead DB fails fast instead of hanging
- [x] 2. Startup survives an unreachable DB (`init_db()` failure is logged, not fatal)
- [x] 3. Every route closes its connection, even on errors (`db_cursor()` context manager)
- [x] Verify: all pages render locally against Supabase, duplicate-exercise path,
      unreachable DB → startup OK + fast failure, connections closed on exceptions
- [x] 4. gunicorn: added to requirements.txt, render.yaml startCommand updated
- [x] Deploy: push to main (b64d1ed), set Start Command in Render dashboard, verify
      `x-render-origin-server` header shows gunicorn instead of Werkzeug
      → live on gunicorn since 10:50; all 5 pages 200 in 0.4–0.75s, no errors

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
