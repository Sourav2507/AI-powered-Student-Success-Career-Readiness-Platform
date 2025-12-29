import os
import requests

def fetch_jobs_from_adzuna(role, location="india"):
    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
    ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise RuntimeError("Adzuna API credentials not set")

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": 10,
        "what": role,
        "where": location,
        "content-type": "application/json"
    }

    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    jobs = []
    for j in data.get("results", []):
        jobs.append({
            "title": j.get("title"),
            "company": j.get("company", {}).get("display_name"),
            "location": j.get("location", {}).get("display_name"),
            "url": j.get("redirect_url"),
            "salary": j.get("salary_min")
        })

    return jobs
