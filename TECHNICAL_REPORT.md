# Technical Report: Resolv DRS — System Architecture, Frontend/Backend, and Tech Stack

**Project:** Autonomous Supply Chain Resilience Agent (Resolv DRS)  
**Date:** March 6, 2026

---

## 1. System Architecture

### 1.1 Conceptual Design (Target Architecture)

The project is designed around an **agent-based architecture** aligned with the challenge requirements:

- **Perception → Reasoning → Planning → Action pipeline**: The agent is intended to perceive disruption signals, reason about trade-offs, plan mitigations, and execute or draft actions.
- **Modular design**: Clear separation between perception (news ingestion, ERP signals, supplier health), risk intelligence (scoring, impact modeling), planning (simulation, optimization), and autonomous action (emails, ERP adjustments, escalations).
- **Memory & feedback loop**: Logs past disruptions and outcomes to improve future recommendations (`logs/runs.jsonl`).
- **Explainability**: Reasoning traces, risk justification, and human override thresholds are part of the design.

### 1.2 Implemented Architecture

The current implementation uses a **hybrid, decoupled architecture**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Astro)                                    │
│  ┌─────────────────────┐  ┌──────────────────────────────────────────────┐  │
│  │ Marketing / Docs    │  │ DRS Studio (/drs)                             │  │
│  │ - Landing (/)       │  │ - Client-side SPA-like single page             │  │
│  │ - Blog, Products    │  │ - Direct API calls: Gemini, NewsData           │  │
│  │ - Starlight docs    │  │ - Local state, no backend API                  │  │
│  └─────────────────────┘  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTPS (client-side)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL APIs (browser → internet)                     │
│  • Google Generative Language API (Gemini)                                   │
│  • NewsData.io (live news feed)                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Python, CLI-based)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ supplychain-agent/                                                    │   │
│  │   - Google ADK agent (root_agent)                                     │   │
│  │   - Tools: compute_stockout_risk, load_alert, load_erp_snapshot       │   │
│  │   - Demo data: alert.json, erp_snapshot.csv                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ scripts/                                                              │   │
│  │   - smoke_run.py: Full agent run → out/latest.json                    │   │
│  │   - validate_output.py: Validates JSON output                         │   │
│  │   - run_prompt.py: Interactive prompt testing                          │   │
│  │   - test_llm.py: Smoke + validate                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  No HTTP server. Runs on-demand via CLI.                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**

- **Static site generation (SSG)**: Astro builds static HTML by default. No server-side rendering for dynamic data.
- **DRS Studio**: A single-page application embedded in `/drs` that runs entirely in the browser. It fetches news from NewsData.io and sends prompts to the Gemini API directly from the client.
- **Backend agent**: Python-based, uses Google ADK and Gemini. Invoked via CLI scripts; not exposed as a web service. Output is written to `out/latest.json` and `logs/runs.jsonl`.
- **No backend API layer**: The frontend does not call a project-owned backend. It talks only to third-party APIs (Gemini, NewsData).
- **Deployment**: Build outputs to `.vercel/output/static`, indicating Vercel deployment. Post-build step (`process-html.mjs`) minifies HTML.

---

## 2. Frontend / Backend Breakdown

### 2.1 Frontend

| Responsibility | Implementation |
|----------------|----------------|
| **Framework** | Astro 5 |
| **Routing** | File-based: `src/pages/*.astro`, `src/pages/fr/*.astro`, dynamic routes `[id].astro` |
| **Layout** | `MainLayout.astro` (Navbar, main slot, FooterSection) |
| **Components** | `src/components/sections/` (landing, features, navbar&footer, testimonials), `src/components/ui/` (buttons, cards, forms, icons) |
| **Styling** | Tailwind CSS v4 (via `@tailwindcss/vite`), global CSS, Starlight custom CSS |
| **Content** | Content collections: blog, products, insights, docs (Starlight) |
| **Interactivity** | Preline (modals, accordions), Lenis (smooth scroll), GSAP (animations), vanilla JS in DRS |
| **i18n** | French locale (`/fr/*`), Starlight locales (de, es, fa, fr, ja, zh-cn) |
| **DRS Studio** | Self-contained in `drs.astro`: inline CSS, inline script, no framework. State in `state` object, DOM updates via `render()`, `compute()`, `ask()`. |

**DRS Studio frontend logic:**

- **News**: Fetches from NewsData.io API when `PUBLIC_NEWSDATA_API_KEY` is set; otherwise uses hardcoded fallback stories.
- **Copilot**: Sends prompts to `https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent` with `PUBLIC_GEMINI_API_KEY`.
- **KPIs**: Computed client-side from news classification (high/medium/low), risk controls (sliders), and profile (concentration, regional exposure, lead-time, buffer, SLA, threshold).
- **Actions**: Simulated action queue and draft outputs (supplier email, ERP adjustment, escalation) derived from local state.

### 2.2 Backend

| Responsibility | Implementation |
|----------------|----------------|
| **Agent runtime** | Python 3, Google ADK (`google.adk`), Google GenAI (`google.genai`) |
| **Agent definition** | `supplychain-agent/my_first_agent/` (or sibling `../supplychain-agent/`) |
| **Execution model** | CLI scripts; no HTTP server |
| **Session** | `InMemorySessionService` for agent runs |
| **Inputs** | `alert.json`, `erp_snapshot.csv`, `data/customer_profile.json` |
| **Outputs** | `out/latest.json`, `logs/runs.jsonl` |
| **Tools** | Stockout risk computation, alert loading, ERP snapshot loading |

**Backend is not integrated with the frontend.** The DRS Studio does not call the Python agent. It uses Gemini directly for the copilot and NewsData for news. The Python agent is used for offline testing and validation.

---

## 3. Tech Stack

### 3.1 Frontend Technologies

| Category | Technology | Version / Notes |
|----------|------------|-----------------|
| **Framework** | Astro | ^5.18.0 |
| **Build** | Vite (via Astro) | — |
| **Styling** | Tailwind CSS | ^4.2.1 |
| **Tailwind plugins** | `@tailwindcss/forms`, `@tailwindcss/typography` | — |
| **Documentation** | Starlight | ^0.37.6 |
| **Content** | MDX | ^4.3.13 |
| **Sitemap** | @astrojs/sitemap | ^3.7.0 |
| **Compression** | astro-compressor (Brotli) | ^1.2.0 |
| **UI components** | Preline | ^4.1.2 |
| **Animations** | GSAP | ^3.14.2 |
| **Smooth scroll** | Lenis | ^1.3.17 |
| **Images** | Sharp | ^0.34.5 |
| **Package managers** | pnpm, npm | Both lockfiles present |
| **Language** | TypeScript | ^5.9.3 |
| **Formatting** | Prettier | ^3.8.1 |

### 3.2 Backend Technologies

| Category | Technology | Notes |
|----------|------------|-------|
| **Language** | Python 3 | — |
| **Agent framework** | Google ADK | `google.adk.runners.Runner`, `google.adk.sessions.InMemorySessionService` |
| **LLM** | Google Gemini | Via `google.genai.types` |
| **Dependencies** | `google-adk`, `google-genai` | Installed via pip |

### 3.3 External Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Google Generative Language API** | Gemini for DRS copilot (frontend) and agent (backend) | `GOOGLE_API_KEY`, `PUBLIC_GEMINI_API_KEY` |
| **NewsData.io** | Live news feed in DRS Studio | `NEWSDATA_API_KEY`, `PUBLIC_NEWSDATA_API_KEY` |
| **Model** | Default: `gemini-2.5-flash` | `PUBLIC_GEMINI_MODEL` |

### 3.4 Data & Configuration

| Type | Location | Format |
|------|----------|--------|
| **Site config** | `src/data_files/constants.ts` | TypeScript |
| **FAQs, features, pricing** | `src/data_files/*.json`, `fr/*.json` | JSON |
| **Content** | `src/content/blog`, `products`, `insights`, `docs` | Markdown, MDX |
| **Agent inputs** | `supplychain-agent/`, `data/` | JSON, CSV |
| **Agent output** | `out/latest.json` | JSON |
| **Run logs** | `logs/runs.jsonl` | JSONL |
| **Environment** | `.env` | Key-value |

### 3.5 Deployment

| Aspect | Technology |
|--------|-------------|
| **Platform** | Vercel (inferred from `process-html.mjs` path `.vercel/output/static`) |
| **Output** | Static HTML, CSS, JS |
| **Post-build** | `process-html.mjs` minifies HTML in output directory |

---

## 4. Summary

| Layer | Technology |
|-------|-------------|
| **Frontend** | Astro 5, Tailwind v4, Preline, Starlight, GSAP, Lenis, vanilla JS (DRS) |
| **Backend** | Python, Google ADK, Gemini (CLI-only) |
| **APIs** | Gemini (Generative Language), NewsData.io |
| **Deployment** | Vercel (static) |

The system is a **static marketing/documentation site** with an embedded **client-side DRS Studio** that calls external APIs directly, plus a **standalone Python agent** for offline supply chain analysis and testing. There is no unified backend API; the frontend and Python agent operate independently.
