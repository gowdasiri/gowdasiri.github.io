#!/usr/bin/env python3
"""Daily U.S. visa-sponsored job discovery pipeline.

Collects jobs from configured providers, enforces strict filters, scores
company hiring sentiment, deduplicates against historical records, and writes
exactly 20 jobs to daily_visa_sponsored_jobs_YYYY-MM-DD.json.
"""
from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TARGET_ROLES = [
    "Data Engineer",
    "Senior Data Analyst",
    "Product Marketing Manager",
    "Product Marketing",
]
REQUIRED_SOURCES = {"LinkedIn", "Indeed", "BuiltIn", "Hired"}
SPONSOR_KEYWORDS = [
    "we sponsor visas",
    "h-1b sponsorship available",
    "open to opt",
    "open to cpt",
    "employment visa sponsorship",
    "sponsor",
    "visa",
    "h-1b",
    "opt",
    "cpt",
    "o-1",
    "e-3",
    "green card",
]
NO_SPONSOR_PATTERNS = [
    "no sponsorship",
    "unable to sponsor",
    "cannot sponsor",
    "do not sponsor",
]
SUPPORTED_VISAS = ["H1B", "OPT", "CPT", "O-1", "E-3", "Green Card"]


@dataclass
class Job:
    job_id: str
    job_title: str
    company: str
    location: str
    posting_date: datetime
    source_platform: str
    job_link: str
    description: str


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _load_json(url: str, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> Any:
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url=url, headers=headers or {})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_jobs_from_endpoint(source_name: str, base_url: str, api_key: str | None) -> list[Job]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    rows = _load_json(base_url, headers=headers)
    jobs: list[Job] = []
    for item in rows:
        try:
            jobs.append(
                Job(
                    job_id=str(item["id"]),
                    job_title=item["title"],
                    company=item["company"],
                    location=item.get("location", ""),
                    posting_date=_parse_datetime(item["posted_at"]),
                    source_platform=source_name,
                    job_link=item["url"],
                    description=item.get("description", ""),
                )
            )
        except KeyError:
            continue
    return jobs


def fetch_jobs() -> list[Job]:
    """Fetch jobs from LinkedIn/Indeed/BuiltIn/Hired via configured endpoints."""
    sources = {
        "LinkedIn": os.getenv("LINKEDIN_JOBS_API_URL"),
        "Indeed": os.getenv("INDEED_JOBS_API_URL"),
        "BuiltIn": os.getenv("BUILTIN_JOBS_API_URL"),
        "Hired": os.getenv("HIRED_JOBS_API_URL"),
    }
    api_key = os.getenv("JOBS_API_KEY")
    jobs: list[Job] = []
    for source, url in sources.items():
        if not url:
            continue
        jobs.extend(fetch_jobs_from_endpoint(source, url, api_key))
    return jobs


def role_match(title: str) -> bool:
    t = title.lower()
    return any(target.lower() in t for target in TARGET_ROLES)


def is_mid_or_senior(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    senior_signals = ["senior", "staff", "lead", "principal", "manager", "mid-level", "5+ years", "3+ years"]
    return any(sig in text for sig in senior_signals)


def in_us_location(location: str) -> bool:
    loc = location.lower()
    return "united states" in loc or " usa" in loc or any(x in loc for x in ["remote", "hybrid", "new york", "california", "texas", "seattle", "boston"])


def sponsorship_from_description(description: str) -> tuple[list[str], bool]:
    lower = description.lower()
    if any(pattern in lower for pattern in NO_SPONSOR_PATTERNS):
        return [], False
    if not any(keyword in lower for keyword in SPONSOR_KEYWORDS):
        return [], False

    found: list[str] = []
    mappings = {
        "H1B": ["h-1b", "h1b"],
        "OPT": ["opt"],
        "CPT": ["cpt"],
        "O-1": ["o-1", "o1"],
        "E-3": ["e-3", "e3"],
        "Green Card": ["green card", "permanent residency"],
    }
    for visa, phrases in mappings.items():
        if any(p in lower for p in phrases):
            found.append(visa)
    return found or SUPPORTED_VISAS, True


def load_dol_sponsors(path: Path) -> set[str]:
    if not path.exists():
        return set()
    sponsors = set()
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("company") or "").strip().lower()
            if name:
                sponsors.add(name)
    return sponsors


def verify_sponsorship(job: Job, dol_sponsors: set[str]) -> tuple[list[str], str] | None:
    visas, desc_ok = sponsorship_from_description(job.description)
    company_match = job.company.strip().lower() in dol_sponsors

    if desc_ok and company_match:
        return visas, "Job Description + DOL Data"
    if desc_ok:
        return visas, "Job Description"
    if company_match and not any(x in job.description.lower() for x in NO_SPONSOR_PATTERNS):
        return ["H1B"], "DOL Data"
    return None


def sentiment_from_endpoint(company: str) -> int:
    """Returns [0..100] sentiment score from endpoint JSON: {"score": int}."""
    endpoint = os.getenv("SENTIMENT_API_URL")
    api_key = os.getenv("SENTIMENT_API_KEY")
    if not endpoint:
        return 0
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    payload = _load_json(endpoint, headers=headers, params={"company": company, "lookback_days": "90"})
    try:
        return int(payload["score"])
    except Exception:
        return 0


def load_seen_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text()))


def save_seen_ids(path: Path, seen: set[str]) -> None:
    path.write_text(json.dumps(sorted(seen), indent=2))


def should_run_now() -> bool:
    if os.getenv("FORCE_RUN") == "1":
        return True
    now_et = datetime.now(tz=ZoneInfo("America/New_York"))
    return now_et.hour == 6


def discover_jobs() -> list[dict[str, Any]]:
    raw_jobs = fetch_jobs()
    dol_sponsors = load_dol_sponsors(Path("data/dol_sponsors.csv"))
    seen_ids = load_seen_ids(Path("data/seen_job_ids.json"))
    now = datetime.now(timezone.utc)

    candidates: list[dict[str, Any]] = []
    for job in raw_jobs:
        if job.job_id in seen_ids:
            continue
        if job.source_platform not in REQUIRED_SOURCES:
            continue
        if now - job.posting_date > timedelta(hours=24):
            continue
        if not role_match(job.job_title):
            continue
        if not is_mid_or_senior(job.job_title, job.description):
            continue
        if not in_us_location(job.location):
            continue
        sponsorship = verify_sponsorship(job, dol_sponsors)
        if not sponsorship:
            continue

        visas, verified_by = sponsorship
        score = sentiment_from_endpoint(job.company)
        if score < 60:
            continue

        candidates.append(
            {
                "job_id": job.job_id,
                "job_title": job.job_title,
                "company": job.company,
                "location": job.location,
                "visa_type_supported": visas,
                "sponsorship_verified_by": verified_by,
                "posting_date": job.posting_date.isoformat(),
                "source_platform": job.source_platform,
                "company_sentiment_score": score,
                "job_link": job.job_link,
                "why_relevant": "Matches target role, U.S. location, recent posting, and verified visa sponsorship.",
            }
        )

    def rank_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
        sponsorship_rank = 0 if "+" in item["sponsorship_verified_by"] else (1 if item["sponsorship_verified_by"] == "Job Description" else 2)
        role_strength = 0 if "senior" in item["job_title"].lower() else 1
        sentiment_rank = -item["company_sentiment_score"]
        recency_rank = item["posting_date"]
        return sponsorship_rank, role_strength, sentiment_rank, recency_rank

    candidates.sort(key=rank_key)
    selected = candidates[:20]

    if len(selected) != 20:
        raise RuntimeError(f"Expected exactly 20 jobs, found {len(selected)} after strict filtering.")

    seen_ids.update(item["job_id"] for item in selected)
    save_seen_ids(Path("data/seen_job_ids.json"), seen_ids)
    for item in selected:
        item.pop("job_id", None)
    return selected


def main() -> None:
    if not should_run_now():
        print("Skipping run because current time is not 6:00 AM ET (use FORCE_RUN=1 to override).")
        return

    output = discover_jobs()
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"daily_visa_sponsored_jobs_{datetime.now(tz=ZoneInfo('America/New_York')).date().isoformat()}.json"
    output_path = out_dir / file_name
    output_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {len(output)} jobs to {output_path}")


if __name__ == "__main__":
    main()
