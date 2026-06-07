# Sandra's Job Application Tracker

A clean, personal Streamlit app to track your job applications across full-time and freelance roles.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app auto-saves to `applications.json` in the same folder.

## Features

- **Pipeline tab** — View all applications with filters by status, type, sector, and search. Edit or delete any entry inline.
- **Add/Edit tab** — Log new applications or update existing ones (company, role, status, salary, recruiter contact, URL, notes, next steps).
- **Analytics tab** — Donut chart by status, bar by sector, area timeline, full-time vs freelance split.
- **Sidebar** — Filters + JSON export/import for backup.

## Fields tracked

| Field | Examples |
|---|---|
| Company | Capitec, Allan Gray, Freelance Client |
| Role | Data Analyst, BI Developer, Risk Consultant |
| Sector | FinTech, Insurance / FSP, Banking, Data & Analytics |
| Type | Full-time, Freelance / Contract |
| Status | Applied → Interview → Offer / Rejected / Ghosted |
| Priority | 🔥 High / ⚡ Medium / 💤 Low |
| Salary range | ZAR 35k–50k / USD 800/mo |
| Location | Remote, Johannesburg, Harare |
| Contact | Recruiter name |
| Next step | "Follow up Fri", "Send portfolio" |
| Notes | Free text |
| Job URL | Link to posting |
