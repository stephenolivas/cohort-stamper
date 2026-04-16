# Close Cohort Stamper

Stamps the **Lead Cohort** custom field on every Close lead with the Monday of the ISO week (Pacific time) the lead was created.

Cohorts power the 30-day and 60-day net win rate reports: every lead from the week of Mon 2026-04-13 shares the value `2026-04-13`, making them trivially groupable in any reporting tool.

## How it works

Two scripts share the same core logic:

| Script | Trigger | Purpose |
|---|---|---|
| `stamp_hourly.py` | Hourly cron via GitHub Actions | Stamps any lead with an empty cohort field |
| `backfill.py` | Manual dispatch via GitHub Actions | One-shot stamp of all existing unstamped leads. Supports `--dry-run`. |

Both scripts use the same Close query (`custom.cf_XXX:null`) to only fetch leads that need stamping, so they're both idempotent and cheap to re-run.

## Setup

1. Add repo secret `CLOSE_API_KEY` with a Close API key that has write access to leads.
2. Run the backfill workflow from the Actions tab with `dry_run: true` first. Review the cohort distribution in the logs.
3. Re-run with `dry_run: false` to actually stamp.
4. The hourly workflow runs automatically once merged to main.

## Configuration

The cohort field ID is hard-coded in `stamp_hourly.py` and `backfill.py`:

```
cf_ahQ2lncntK1fh0uyEjroF6urNKTHgflhQ0bR39voM4D
```

If the field is ever recreated, update this constant in both scripts.

## Cohort definition

- **Week starts Monday** (ISO 8601)
- **Evaluated in `America/Los_Angeles`** — so a lead created Sunday 11pm PT belongs to that week's Monday, not the next
- **Stored as `YYYY-MM-DD` date** — not a formatted string, so sort/filter/range queries just work
- DST transitions and year boundaries are handled correctly (see `cohort.py`)

## Files

- `close_client.py` — shared API client (rate limiting, 429 retry)
- `cohort.py` — the single source of truth for week calculation
- `stamp_hourly.py` — hourly job
- `backfill.py` — one-shot backfill
- `.github/workflows/stamp-hourly.yml` — hourly schedule
- `.github/workflows/backfill.yml` — manual backfill dispatch

## Notes

- Never add threading or concurrency. Close rate-limits hard and the scripts are fast enough without it.
- The hourly job typically completes in under a minute (stamps ~dozens of new leads).
- The first backfill run will take longer depending on how many unstamped leads exist (~0.5s per lead plus pagination).
