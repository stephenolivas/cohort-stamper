"""Hourly cohort stamper.

Finds leads with an empty Lead Cohort field and stamps them with the
Monday of the ISO week (Pacific time) they were created.

Idempotent: leads that already have a cohort are never touched. Safe
to re-run, safe to run alongside the backfill.

Designed to run every hour via GitHub Actions. Typical run stamps
10-50 new leads and completes in well under a minute.
"""

import sys
from close_client import api_get, api_put
from cohort import cohort_for_iso_timestamp

COHORT_FIELD = "cf_ahQ2lncntK1fh0uyEjroF6urNKTHgflhQ0bR39voM4D"
COHORT_KEY = f"custom.{COHORT_FIELD}"

# Only pull fields we actually need — keeps payloads tiny
FIELDS = f"id,date_created,{COHORT_KEY}"


def find_unstamped_leads():
    """Paginate leads where the cohort field is empty.

    Uses Close's query syntax to filter server-side so we don't pull
    leads that are already stamped.
    """
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
        print(f"  fetched {len(leads)} unstamped leads so far...", flush=True)
        if not data.get("has_more"):
            break
        skip += limit

    return leads


def stamp_lead(lead_id, cohort_monday):
    """Write the cohort date to a single lead."""
    api_put(f"/lead/{lead_id}/", {COHORT_KEY: cohort_monday})


def main():
    print("=== Cohort Stamper (hourly) ===", flush=True)
    print("Finding unstamped leads...", flush=True)

    leads = find_unstamped_leads()
    print(f"Found {len(leads)} unstamped leads", flush=True)

    if not leads:
        print("Nothing to do. Exiting.", flush=True)
        return

    stamped = 0
    errors = 0

    for lead in leads:
        lead_id = lead["id"]
        created = lead.get("date_created")
        if not created:
            print(f"  SKIP {lead_id}: no date_created", flush=True)
            continue

        cohort = cohort_for_iso_timestamp(created)
        try:
            stamp_lead(lead_id, cohort)
            stamped += 1
            print(f"  stamped {lead_id} -> {cohort} (created {created})", flush=True)
        except Exception as e:
            errors += 1
            print(f"  ERROR {lead_id}: {e}", flush=True)

    print(f"\nDone. Stamped {stamped} leads, {errors} errors.", flush=True)

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
