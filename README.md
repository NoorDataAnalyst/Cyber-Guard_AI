# 🛡️ CyberGuard AI — Cyberbullying Detection & RAG Governance

> A production-grade, multi-signal cyberbullying detection system powered by Toxic-BERT, RoBERTa emotion classifiers, 3-index FAISS RAG retrieval, and an LLM reasoning agent (Gemini / Claude) — with a full governance layer, dual-backend persistence (Supabase Postgres + SQLite), and a modular Streamlit UI.

---

## 📸 Overview

| Feature | Implementation |
|---|---|
| **Signal Layer** | `toxic-bert` (toxicity) + `roberta-go-emotions` (emotion) |
| **RAG Retrieval** | 3-index FAISS: thread context, precedent examples, legal policy |
| **LLM Reasoning** | Gemini Flash / Anthropic Claude structured verdict agent |
| **Policy Engine** | Severity → action rules (warn / mute 30-min / block) |
| **Persistence** | SQLAlchemy ORM — Supabase Postgres or local SQLite fallback |
| **Governance** | Admin dashboard, manual overrides, appeal workflow |
| **Analytics** | Plotly charts — severity donut, category bar, detection gauge |
| **UI** | Streamlit + `streamlit-option-menu` horizontal nav, dark glassmorphism |

---

## 🚀 Quickstart (Local Development)

### 1. Clone & create a virtual environment

```bash
git clone <your-repo-url>
cd cyberbullying-detector
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` → `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**`.env` keys:**

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | `gemini` or `anthropic` |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `ANTHROPIC_API_KEY` | Your Anthropic Claude API key |
| `ADMIN_PASSWORD` | Password to unlock the Admin Dashboard |
| `DATABASE_URL` | *(Optional)* Supabase Postgres connection string — leave blank for local SQLite |

### 4. Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

---

## ☁️ Supabase Setup (Production Persistence)

To use **Supabase Postgres** instead of local SQLite:

### Step 1 — Create a Supabase project

1. Go to [https://supabase.com](https://supabase.com) and create a new project.
2. Navigate to **Settings → Database → Connection string → URI**.
3. Copy the `postgres://...` connection string.

### Step 2 — Configure the connection string

**Option A: `.env` file (local development)**

```env
DATABASE_URL=postgresql://postgres:<your-password>@db.<your-project-ref>.supabase.co:5432/postgres
```

> ⚠️ Replace `postgres://` with `postgresql://` if needed — SQLAlchemy 2.0 requires `postgresql://`.

**Option B: Streamlit Cloud secrets (deployment)**

In your Streamlit Cloud dashboard → App settings → Secrets, add:

```toml
DATABASE_URL = "postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres"
ADMIN_PASSWORD = "your_secure_admin_password"
GEMINI_API_KEY = "your_gemini_key"
```

### Step 3 — Tables are auto-created

SQLAlchemy will automatically run `CREATE TABLE IF NOT EXISTS` for all ORM models on first launch. No manual migrations needed.

---

## ☁️ Streamlit Cloud Deployment

1. Push your repo to GitHub.
2. Go to [https://share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch, and set **Main file path** to `app.py`.
4. Under **Advanced settings → Secrets**, paste your secrets in TOML format (see above).
5. Click **Deploy**.

> **Tip:** Add `.env` and `.streamlit/secrets.toml` to your `.gitignore` — never commit credentials!

---

## 🔑 Admin Dashboard

The **Admin Governance Dashboard** is accessible within the **Home** tab → **Admin Governance Dashboard** sub-tab.

- Enter the `ADMIN_PASSWORD` from your `.env` / Streamlit secrets to unlock.
- Once authenticated, the session persists for the browser session (`st.session_state["is_admin"]`).
- Admin capabilities:
  - **Approve or Reject** user account appeals (blocked users can submit appeals from the Live Feed)
  - **Force Block / Unblock** users from the flagged verdict audit table
  - **Dismiss flags** that are false positives
  - Add **admin notes** to all override actions (all logged in the `actions` table)

---

## 🧪 Running Tests

All tests use **in-memory SQLite** — no live Supabase connection or API keys required.

```bash
# Run the full test suite
python tests/run_all_tests.py

# Or run specific new test modules with pytest
pytest tests/test_db_sqlalchemy.py -v
pytest tests/test_appeals.py -v

# Run all tests with pytest
pytest tests/ -v
```

### Test modules

| File | Covers |
|---|---|
| `test_db_sqlalchemy.py` | SQLAlchemy ORM CRUD — users, messages, analytics, restrictions |
| `test_appeals.py` | Full appeal workflow — create, get_pending, approve, reject, edge cases |
| `test_pipeline.py` | Pipeline flow — restriction pre-check, verdict dispatch |
| `test_policy.py` | Policy engine — severity → action rules, admin overrides |
| `test_preprocessing.py` | Text cleaning and normalization |
| `test_toxicity.py` | Toxicity classifier outputs |
| `test_emotion.py` | Emotion classifier outputs |
| `test_retrieval.py` | FAISS RAG retrieval correctness |
| `test_llm_agent.py` | LLM agent verdict structure |
| `test_db.py` | Legacy DB helper compatibility |

---

## 📁 Project Structure

```
cyberbullying-detector/
├── app.py                      ← Thin Streamlit router (option-menu nav)
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
├── src/
│   ├── config.py               ← Constants, paths, severity levels
│   ├── db.py                   ← SQLAlchemy ORM + dual-backend persistence
│   ├── pipeline.py             ← 8-step detection pipeline
│   ├── policy.py               ← Severity → action rules, admin overrides
│   ├── preprocessing.py        ← Text cleaning
│   ├── toxicity_classifier.py  ← toxic-bert inference
│   ├── emotion_classifier.py   ← roberta-go-emotions inference
│   ├── retrieval.py            ← 3-index FAISS RAG retrieval
│   ├── llm_agent.py            ← Gemini / Claude LLM reasoning agent
│   └── ui/
│       ├── home.py             ← Live Feed + Admin Governance Dashboard
│       ├── stats.py            ← Plotly Analytics tab
│       ├── features.py         ← Feature overview tab
│       ├── tech_stack.py       ← Technology stack tab
│       ├── team.py             ← Team & Acknowledgements tab
│       └── about.py            ← About & legal disclaimer tab
├── data/
│   ├── examples/               ← Cyberbullying precedent corpus
│   └── policy/                 ← PECA 2016 / FIA policy snippets
└── tests/
    ├── test_appeals.py         ← Appeal workflow tests
    ├── test_db_sqlalchemy.py   ← ORM persistence tests
    ├── test_pipeline.py
    ├── test_policy.py
    └── ...
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `users` | Identity registry (`user_id`, `username`, `status`) |
| `messages` | Every sent message with toxicity/emotion scores |
| `verdicts` | LLM verdict per flagged message (category, severity, RAG context JSON) |
| `actions` | Immutable audit log of all system/admin actions |
| `restricted_users` | Active block/mute records with `mute_expires_at` for 30-min auto-expiry |
| `appeals` | User-submitted appeal records with admin resolution |

---

## ⚖️ Legal Notice

This system references Pakistan's **Prevention of Electronic Crimes Act (PECA) 2016** and **FIA Cyber Crime Wing** policy corpus for educational and research purposes only. It is not a substitute for professional legal advice.

* [Prevention of Electronic Crimes Act (PECA) 2016 - National Assembly of Pakistan](https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-apaUY2Jvbp8%253D-sg-jjjjjjjjjjjjj).
* [FIA Cyber Crime Wing Guidelines & Publications](https://www.fia.gov.pk/files/publications/860464251.pdf)

---

## 📝 License

MIT License — See [LICENSE](LICENSE) file for details.
