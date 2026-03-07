# Autonomous Supply Chain Resilience Agent

AI co-pilot for mid-market manufacturing: monitors disruptions, assesses risk, and recommends mitigations using Google ADK and Gemini.

This repo combines:
- **Backend**: Python agent (Google ADK, Gemini)
- **Frontend**: Astro site with Resolv DRS Studio (`/drs`)

---

## Quick Start

### Frontend (Astro)

```bash
cp .env.example .env   # Edit with your API keys
pnpm install
pnpm dev
```

Open http://localhost:4321. Visit `/drs` for the DRS Studio command center.

### Backend (Python agent)

```bash
pip install google-adk google-genai
python scripts/smoke_run.py
```

---

## Environment Variables

Create `.env` in the repo root. See `.env.example` for the full list.

| Variable | Used by | Purpose |
|----------|---------|---------|
| `GOOGLE_API_KEY` | Backend | Gemini for agent runs |
| `NEWSDATA_API_KEY` | Backend | News data (optional) |
| `PUBLIC_GEMINI_API_KEY` | Frontend | DRS Studio copilot (client-side) |
| `PUBLIC_NEWSDATA_API_KEY` | Frontend | Live news feed in DRS Studio |
| `PUBLIC_GEMINI_MODEL` | Frontend | Model name (default: gemini-2.5-pro) |

---

## Backend: Testing the Agent

### 1. Smoke run (end-to-end)

```bash
python scripts/smoke_run.py
```

- Loads agent from `supplychain-agent/my_first_agent/`
- Uses `alert.json`, `erp_snapshot.csv`, `data/customer_profile.json`
- Writes output to `out/latest.json`, logs to `logs/runs.jsonl`

### 2. Output validation

```bash
python scripts/validate_output.py
```

### 3. Scenario testing

- Edit `supplychain-agent/my_first_agent/alert.json` for different disruptions
- Edit `data/customer_profile.json` for different customer profiles
- Edit `supplychain-agent/my_first_agent/erp_snapshot.csv` for inventory/demand changes

---

## Frontend: DRS Studio

The `/drs` page is the Resolv DRS Studio – an autonomous supply chain resilience command system with:

- **Dashboard**: KPIs, live news, system summary
- **Intelligence**: News feed, signal monitor
- **Copilot**: Gemini-powered mitigation chat
- **Actions**: Action queue, draft outputs
- **Controls**: Risk controls, governance

Set `PUBLIC_GEMINI_API_KEY` and `PUBLIC_NEWSDATA_API_KEY` in `.env` for full functionality.

---

## Project Layout

```
├── supplychain-agent/     # Backend: Agent definition, tools, demo data
├── scripts/               # Backend: smoke_run, validate_output, etc.
├── data/                  # Backend: customer_profile.json
├── out/                   # Backend: latest.json output
├── logs/                  # Backend: runs.jsonl
├── src/                   # Frontend: Astro pages, components
├── public/                # Frontend: static assets
├── astro.config.mjs        # Frontend: Astro config
└── package.json           # Frontend: Node deps
```

---

## Troubleshooting

- **`GOOGLE_API_KEY` not set**: Create `.env` with `GOOGLE_API_KEY=...`
- **Import error for `my_first_agent`**: Run scripts from repo root
- **DRS Studio fallback mode**: Set `PUBLIC_GEMINI_API_KEY` and `PUBLIC_NEWSDATA_API_KEY` in `.env`
