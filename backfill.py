"""One-time backfill of the Lead Cohort field.

Run this ONCE before enabling the hourly stamper. It stamps every
existing lead that doesn't already have a cohort. Leads that predate
the field being created will be stamped based on their date_created,
same as any other lead.

Usage:
    python3 -u backfill.py --dry-run    # count what would be stamped
    python3 -u backfill.py              # actually stamp

Mechanically identical to stamp_hourly.py except:
  - no sys.exit(1) on partial failure (we want to power through and
    let you re-run; the hourly will clean up anything missed anyway)
  - supports --dry-run
  - prints a cohort distribution summary at the end
"""

import sys
from collections import Counter
from close_client import api_get, api_put
from cohort import cohort_for_iso_timestamp

COHORT_FIELD = "cf_ahQ2lncntK1fh0uyEjroF6urNKTHgflhQ0bR39voM4D"
COHORT_KEY = f"custom.{COHORT_FIELD}"
FIELDS = f"id,date_created,{COHORT_KEY}"


def find_unstamped_leads():
    """Same logic as the hourly — only fetch leads without a cohort."""
    leads = []
    skip = 0
    limit = 100

    while True:
        data = api_get("/lead/", params={
            "query": f"custom.{COHORT_FIELD}:null sort:date_created",
            "_fields": FIELDS,
            "_skip": skip,
            "_limit": limit,
        })
        batch = data.get("data", [])
        if not batch:
            break
        leads.extend(batch)
        if len(leads) % 1000 == 0 or not data.get("has_more"):
            print(f"  fetched {len(leads)} unstamped leads...", flush=True)
        if not data.get("has_more"):
            break
        skip += limit

    return leads


def main():
    dry_run = "--dry-run" in sys.argv

    print("=== Cohort Backfill ===", flush=True)
    print(f"Mode: {'DRY RUN (no writes)' if dry_run else 'LIVE (will write)'}", flush=True)
    print("Finding unstamped leads...", flush=True)

    leads = find_unstamped_leads()
    print(f"Found {len(leads)} unstamped leads\n", flush=True)

    if not leads:
        print("Nothing to do. Exiting.", flush=True)
        return

    # Pre-compute every cohort so we can show distribution before writing
    cohort_counts = Counter()
    skipped = 0
    for lead in leads:
        created = lead.get("date_created")
        if not created:
            skipped += 1
            continue
        cohort_counts[cohort_for_iso_timestamp(created)] += 1

    print("Cohort distribution:")
    for cohort in sorted(cohort_counts.keys()):
        print(f"  {cohort}: {cohort_counts[cohort]:>6} leads")
    print(f"  (skipped {skipped} leads with no date_created)\n")

    if dry_run:
        print("DRY RUN — no writes performed. Re-run without --dry-run to stamp.", flush=True)
        return

    print("Writing cohorts to Close...", flush=True)
    stamped = 0
    errors = 0
    total = len(leads)

    for i, lead in enumerate(leads, 1):
        lead_id = lead["id"]
        created = lead.get("date_created")
        if not created:
            continue

        cohort = cohort_for_iso_timestamp(created)
        try:
            api_put(f"/lead/{lead_id}/", {COHORT_KEY: cohort})
            stamped += 1
        except Exception as e:
            errors += 1
            print(f"  ERROR {lead_id}: {e}", flush=True)

        if i % 100 == 0:
            print(f"  progress: {i}/{total} ({stamped} stamped, {errors} errors)", flush=True)

    print(f"\nDone. Stamped {stamped} leads, {errors} errors.", flush=True)
    if errors > 0:
        print("Re-run the script to retry errors (only unstamped leads will be processed).",
              flush=True)


if __name__ == "__main__":
    main()
