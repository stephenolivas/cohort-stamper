from close_client import api_get

COHORT_FIELD = "cf_ahQ2lncntK1fh0uyEjroF6urNKTHgflhQ0bR39voM4D"

queries_to_test = [
    f"custom.{COHORT_FIELD}:null",
    f"-has:custom.{COHORT_FIELD}",
    f"custom.{COHORT_FIELD}:\"\"",
    "",  # no filter at all — should return everything
]

for q in queries_to_test:
    data = api_get("/lead/", params={
        "query": q,
        "_fields": "id",
        "_limit": 1,
    })
    total = data.get("total_results", "?")
    print(f"Query: {q!r:60} -> total_results: {total}")
