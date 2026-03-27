# Agentic AI Resume Screening System

Production-style, multi-agent resume screening app with:

- Streamlit SaaS-style dashboard UI (sidebar navigation, charts, candidate profile)
- True multi-agent pipeline (parsing → skills → experience → matching → scoring → ranking → recommendations → analytics)
- SQLite persistence via SQLModel (swap to Postgres by setting `RESUME_DB_URL`)
- Batch resume processing with parallel workers
- Explainable ranking + skill-gap analysis

## Quickstart (Windows / PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Database

Default is SQLite file `resume_screening.db` in the project root.

To use Postgres:

```powershell
$env:RESUME_DB_URL="postgresql+psycopg://user:pass@localhost:5432/resume"
```

If you change models and your local SQLite schema is out of date, delete `resume_screening.db` and rerun.

