# Automated Daily Visa-Sponsored Job Discovery

This repository now includes a scheduled pipeline that discovers **exactly 20 new jobs daily** for:
- Data Engineer
- Senior Data Analyst
- Product Marketing Manager / Product Marketing

## How it works

`job_discovery.py` enforces all required filters:
1. posted in last 24h
2. U.S. location only
3. mid/senior level only
4. sponsorship high-confidence only (job description and/or DOL sponsor list)
5. sentiment score >= 60 (90-day hiring sentiment)
6. dedupe against historical IDs (`data/seen_job_ids.json`)
7. strict output count = exactly 20 or fail

## Required integrations

Set these repository secrets for the GitHub Action:
- `LINKEDIN_JOBS_API_URL`
- `INDEED_JOBS_API_URL`
- `BUILTIN_JOBS_API_URL`
- `HIRED_JOBS_API_URL`
- `JOBS_API_KEY` (optional if endpoints are public)
- `SENTIMENT_API_URL`
- `SENTIMENT_API_KEY` (optional)

Each jobs endpoint must return an array of objects with:
- `id`
- `title`
- `company`
- `location`
- `posted_at` (ISO-8601)
- `url`
- `description`

Sentiment endpoint must return:
```json
{ "score": 78 }
```

## Schedule

Workflow runs hourly and executes only at **6:00 AM America/New_York** (DST-safe) unless `FORCE_RUN=1`.

## Output

Saved to:
- `outputs/daily_visa_sponsored_jobs_YYYY-MM-DD.json`

Each entry has the required JSON schema fields.
