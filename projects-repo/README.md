# projects-repo

Starter scaffold intended to become its **own standalone Git repository**.

## Does this run automatically?

- **No**. Nothing runs automatically until you run a script yourself or set up a scheduler.
- To create your own repo from this scaffold:

```bash
cp -R projects-repo <your-new-repo-name>
cd <your-new-repo-name>
./init-standalone-repo.sh
```

## What should you check after setup?

- `git status` is clean
- `git branch --show-current` is `main`
- Your remote is set correctly (if using GitHub): `git remote -v`

## Generate LinkedIn job links (click-and-apply workflow)

This scaffold can generate **LinkedIn job search links** you can click directly.

> It does **not** auto-apply to jobs. You still review and submit applications manually.

### 1) Create your config

```bash
cp job-search-config.example.json job-search-config.json
# edit job-search-config.json with your own keywords and locations
```

### 2) Generate links

```bash
python3 generate_linkedin_links.py --config job-search-config.json --out job-links.csv
```

Open `job-links.csv` and click URLs.

## Schedule daily at 8:00 PM EST/ET

Use the helper script:

```bash
./schedule-8pm-est.sh
```

Then verify:

```bash
crontab -l
```

This installs a daily cron job at 8:00 PM in `America/New_York` timezone and writes outputs under `output/`.

## Files included

- `src/` and `tests/` placeholders
- `.gitignore`
- `LICENSE` (MIT)
- `init-standalone-repo.sh`
- `generate_linkedin_links.py`
- `job-search-config.example.json`
- `schedule-8pm-est.sh`
