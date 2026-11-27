# ðŸ’¸ AI-First Personal Expense Tracker

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq%20(gpt--oss--120b)-F55036)
![Pydantic](https://img.shields.io/badge/Validation-Pydantic%20v2-E92063?logo=pydantic&logoColor=white)

> **A local-first personal finance application that pairs deterministic accounting with Pydantic-validated AI batch extraction, human-in-the-loop review, and zero-hallucination spending insights.**

---

## ðŸ—ï¸ System Architecture & AI Guardrails

Rather than letting an LLM write directly to storage or perform raw arithmetic, the system enforces a strict boundary between **probabilistic AI parsing** and **deterministic financial state**:

```text
  [Natural Language Input]                        [Manual Expense Form]
            â”‚                                               â”‚
            â–¼                                               â”‚
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                                     â”‚
  â”‚   Groq LLM API    â”‚  (temperature=0, JSON mode)         â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                     â”‚
            â–¼                                               â”‚
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                                     â”‚
  â”‚  Pydantic Schema  â”‚  (ExpenseBatch: types, enums, >0)   â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                     â”‚
            â–¼                                               â”‚
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                                     â”‚
  â”‚ Human-in-the-Loop â”‚  (st.data_editor review/edit)       â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                     â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â–¼
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚ Atomic JSON Storage   â”‚  (os.replace -> expenses.json)
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â–¼                                               â–¼
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ Deterministic UI  â”‚  (Current Month KPIs,     â”‚ Grounded AI Coach â”‚
  â”‚ & Filtered Charts â”‚   Budget Bar, CSV Export) â”‚ (Python-verified  â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                           â”‚  JSON totals)     â”‚
                                                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## ðŸš€ How to Run It

### 1. Prerequisites
- **Python 3.10+**
- **Groq API Key (`GROQ_API_KEY`)** â€” required for AI Quick-Add and AI Spending Summary *(manual entry, filtering, budget tracking, charts, and CSV export work offline without an API key)*.

### 2. Clone & Install Dependencies
```bash
# 1. Clone the repository
git clone [https://github.com/](https://github.com/)Alfahadshahi007/ai-expense-tracker.git
cd ai-expense-tracker

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` in the project root and add your Groq API key:
```bash
# Windows PowerShell:
copy .env.example .env
# macOS / Linux:
cp .env.example .env
```
Edit `.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 4. Launch the Application
```bash
python -m streamlit run app.py
```
Navigate to `http://localhost:8501`. Click **Load Sample Expenses** in the left sidebar to populate multi-month transactions immediately.

---

## âš–ï¸ Stack Choices & Trade-Offs

| Layer | Technology Choice | Why It Was Chosen | Trade-Off Accepted |
| :--- | :--- | :--- | :--- |
| **UI Framework** | **Streamlit** | Rapid single-file reactive UI with native forms, `st.data_editor` for human-in-the-loop review, KPI metric cards, progress bars, and charts. | Full-script reruns on widget interaction; would migrate to **FastAPI + React** for complex multi-user SPA routing. |
| **LLM Inference** | **Groq (`openai/gpt-oss-120b`)** | Sub-second inference latency makes multi-item natural-language expense extraction feel instantaneous during interactive workflows. | Requires external API connectivity for AI features (mitigated via deterministic manual form fallback). |
| **Schema Validation** | **Pydantic (`BaseModel`)** | Enforces strict data contracts (`amount > 0`, `YYYY-MM-DD` `date`, closed `Literal` categories) on LLM JSON outputs before storage. | Slight extra boilerplate vs. raw `json.loads()`, but prevents malformed LLM outputs from corrupting financial records. |
| **AI Grounding** | **Pre-Computed JSON Context Injection** | Python computes exact totals, category aggregations, and remaining monthly budget first, injecting verified JSON into the prompt to eliminate math hallucinations. | Bounded by prompt context window (line items capped at 50 filtered transactions per summary call) rather than semantic search over massive datasets. |
| **Persistence** | **Local JSON (`expenses.json`) + Atomic Write (`os.replace`)** | Zero database setup overhead, human-readable records, legacy key normalization, and crash-safe atomic file replacement. | Single-user local concurrency only; lacks relational indexing and multi-tenant isolation. |

---

## ðŸ“‹ What's Done vs. What's Skipped

> Scoped intentionally to deliver end-to-end reliability, strict AI guardrails, and zero-setup local execution without over-engineering an MVP.

### âœ… Done (Implemented & Verified)

| Feature Area | Implementation Details |
| :--- | :--- |
| **Dual Expense Capture** | **Manual Form** with strict field validation (`Title`, `Amount > 0`, `Category`, `Date` defaulting to today, `Note`) + **AI Quick-Add** supporting multi-expense batch extraction from natural language. |
| **Human-in-the-Loop AI Guardrail** | Groq (`openai/gpt-oss-120b`) extracts structured JSON validated against Pydantic `ExpenseBatch` schemas, rendering an editable `st.data_editor` confirmation grid (with post-edit `YYYY-MM-DD` validation) before saving. |
| **Current Month Summary & Budget** | Dedicated current-month KPIs (total spend, remaining budget against configurable sidebar `Monthly Budget (â‚¹)`, transaction count, top category), live `st.progress` bar, overspend alert, and category breakdown. |
| **Sorted & Multi-Filtered Ledger** | Chronologically sorted newest-first (`date` descending), filterable by **Category**, **Date Range** (`From Date` / `To Date` with inverted-range warning), and case-insensitive **Partial Title Match**, paired with a category bar chart and 1-click CSV export. |
| **Grounded AI Financial Coach** | Pre-computes exact Python totals, category aggregations, and remaining monthly budget into a verified JSON payload so the LLM summarizes spending and answers questions with zero math hallucinations. |
| **Data Hygiene & Demo Utilities** | Normalized `snake_case` schema with legacy key auto-migration, crash-safe atomic JSON writes (`os.replace`), single-entry deletion, and a 1-click **Load Sample Expenses** generator. |

### â­ï¸ Skipped (Intentionally Out of Scope for MVP)

| Deferred Feature | Architectural Rationale |
| :--- | :--- |
| **Authentication & Multi-User Accounts** | Scoped as a single-user local-first application to keep setup instantaneous (`streamlit run app.py`) and focus engineering effort on core workflows and AI reliability. |
| **Vector Database RAG (Chroma / FAISS)** | Structured financial transactions fit cleanly in context alongside exact Python aggregations; vector embeddings would fragment rows and degrade numerical accuracy. |
| **Inline Historical Edits & Recurring Rules** | Users can edit AI-extracted drafts before saving and delete saved entries; full in-place editing of historical ledger rows and automated recurring billing schedules were deferred. |
| **Multi-Currency Live FX Conversion** | Standardized on local currency (`INR â‚¹`) to avoid external exchange-rate API dependencies and floating-point conversion drift. |

---

## âš ï¸ Known Rough Edges & Production Roadmap

> Honest architectural trade-offs identified in the current MVP, paired with concrete fixes for production hardening:

| Severity | Area | Current Behavior (Rough Edge) | Production Fix |
| :---: | :--- | :--- | :--- |
| ðŸŸ¡ **Medium** | **AI Preview Grid Date Widget** | While post-edit validation catches invalid `YYYY-MM-DD` strings cleanly on save, the `date` column in `st.data_editor` still renders as a text field rather than a visual date picker. | Cast draft dates to `datetime.date` objects and bind `st.column_config.DateColumn(format="YYYY-MM-DD", required=True)` for native calendar selection. |
| ðŸŸ¡ **Medium** | **AI Summary Context Cap (50 Rows)** | `summarize_expenses_with_ai` computes exact totals and category rollups across **100%** of matching rows (keeping arithmetic accurate), but truncates individual transaction line items passed to the prompt to the 50 most recent entries to stay within token budgets. | Pair pre-computed category rollups with a top-N outlier extractor or Pandas/SQL query tool for deep historical queries over multi-year logs. |
| ðŸŸ¢ **Low** | **Single-File JSON Persistence** | `expenses.json` with atomic `os.replace()` prevents crash corruption and requires zero setup, but loads all records into memory and lacks multi-user write locking. | Migrate storage to **SQLite** (local) or **PostgreSQL** (multi-tenant) with composite indexes on `(date, category)`. |
| ðŸŸ¢ **Low** | **Ephemeral Sidebar Budget & Stale Summary** | The sidebar `Monthly Budget (â‚¹)` resets to `â‚¹10,000.00` on browser reload, and an already-generated AI summary remains displayed until regenerated even if table filters change. | Persist budget preferences in a companion `settings.json` file and invalidate `st.session_state.ai_summary` on filter state changes. |
| ðŸŸ¢ **Low** | **Fixed 5-Category Taxonomy** | Pydantic enforces a closed 5-category `Literal` (`Food`, `Transport`, `Shopping`, `Entertainment`, `Other`), causing recurring bills, healthcare, and subscriptions to group under `Other`. | Extend the schema enum to include `Bills & Utilities`, `Health`, and `Subscriptions`, or support user-defined custom categories. |
