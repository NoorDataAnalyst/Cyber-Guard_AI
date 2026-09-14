# 🛡️ CyberGuard AI — Cyberbullying Detection & RAG Governance Platform

> A production-grade, multi-signal cyberbullying detection system powered by Toxic-BERT, RoBERTa emotion classifiers, 3-index FAISS RAG retrieval, and an LLM reasoning agent (Gemini / Claude) — with a full governance layer, dual-backend persistence (Supabase Postgres + SQLite), and a modular Streamlit UI.

---

## 👥 Meet the Team

| Team Member | Role | LinkedIn Profile |
|---|---|---|
| **Hira Saleem** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/hira-saleem-595496180/) |
| **Muhammad Usman** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/iusman07/) |
| **Peer Talha Dawood** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/peer-talha-khan-2b1911228/) |
| **Shumail Iqbal** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/shumail-iqbal-4ab23b431/) |
| **Noor ul Ain Zahid** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/noor-ul-ain-zahid-588895341/) |
| **Zeeshan Ahmad** | Contributor | [LinkedIn Profile](https://www.linkedin.com/in/zeeshier/) |

---

## 📸 Overview

| Feature | Implementation |
|---|---|
| **Signal Layer** | `unitary/toxic-bert` (toxicity) + `SamLowe/roberta-base-go_emotions` (emotion) |
| **RAG Retrieval** | 3-index FAISS: thread context, precedent dataset examples, legal policy corpus |
| **LLM Reasoning** | Gemini Flash / Anthropic Claude structured verdict agent with grounded fallback |
| **Policy Engine** | Severity → action rules (soft warning / mute 30-min / block message & suspension) |
| **Persistence** | SQLAlchemy ORM — Supabase Postgres or local SQLite fallback |
| **Governance** | Admin dashboard, manual overrides, appeal review workflow, live chat monitor |
| **Analytics** | Plotly charts — severity donut, category bar, detection rate gauge |
| **UI** | Streamlit + `streamlit-option-menu` horizontal nav, responsive dark glassmorphism |

---

## 🚀 Quickstart (Local Development)

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/ihirasaleem/Cyber-Guard_AI.git
cd Cyber-Guard_AI

python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
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

| Variable | Description | Default / Example |
|---|---|---|
| `ADMIN_EMAIL` | Admin account email for initial seeding and governance access | `[EMAIL_ADDRESS]` |
| `ADMIN_USERNAME` | Admin account username | `Admin` |
| `ADMIN_PASSWORD` | Admin account login password | `[ADMIN_PASSWORD]` | 
| `GEMINI_API_KEY` | *(Optional)* Your Google Gemini API key | `AIzaSy...` |
| `ANTHROPIC_API_KEY` | *(Optional)* Your Anthropic Claude API key | `sk-ant-...` |
| `DATABASE_URL` | *(Optional)* Supabase Postgres connection string — leave blank for local SQLite | `postgresql://user:pass@ep-xxx.supabase.co:6543/postgres` |
| `DATABASE_PATH` | Local SQLite database fallback file path | `data/cyberbullying.db` |
| `TOXICITY_THRESHOLD` | Signal layer toxicity threshold (0.0 to 1.0) | `0.50` |
| `EMOTION_THRESHOLD` | Signal layer emotion threshold (0.0 to 1.0) | `0.30` |

### 4. Run the app

```bash
streamlit run app.py
```

 The app will be available at `http://localhost:8501`.
 
 Link for streamlit Deployed app: https://cyber-guardai.streamlit.app/
 
---

## ☁️ Supabase Setup (Production Persistence)

To use **Supabase Postgres** instead of local SQLite:

### Step 1 — Create a Supabase project

1. Go to [https://supabase.com](https://supabase.com) and create a new project.
2. Navigate to **Project Settings → Database → Connection string → URI**.
3. Copy the `postgres://...` connection string.

### Step 2 — Configure the connection string

**Option A: `.env` file (local development)**

```env
DATABASE_URL=postgresql://postgres.<project-ref>:<your-password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

> ⚠️ Replace `postgres://` with `postgresql://` if needed — SQLAlchemy 2.0 requires `postgresql://`.

**Option B: Streamlit Cloud secrets (deployment)**

In your Streamlit Cloud dashboard → App settings → Secrets, add:

```toml
ADMIN_EMAIL = "your_admin_email_here"
ADMIN_USERNAME = "your_admin_username_here"
ADMIN_PASSWORD = "your_admin_password_here"

GEMINI_API_KEY = "your_gemini_key"
ANTHROPIC_API_KEY = "your_anthropic_key"

DATABASE_URL = "postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres"
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

> 💡 **Tip:** Add `.env` and `.streamlit/secrets.toml` to your `.gitignore` — never commit credentials!

---

## 🔑 Accessing Admin & User Accounts

### 👑 Administrator Account Access
- **Email**: *(as set in `ADMIN_EMAIL`)*
- **Username**: *(as set in `ADMIN_USERNAME`)*
- **Password**: *(as set in `ADMIN_PASSWORD`)*

**Capabilities**:
- Access the **Administrator Governance Dashboard**.
- **🚨 Pending Appeals Review**: Approve or reject user account ban appeals.
- **📋 Flagged Message Audits**: Inspect multi-signal classifier verdicts, LLM reasoning explanations, and execute manual block/unblock overrides.
- **💬 Live Chat Monitor**: Monitor real-time conversation thread.
- **📊 System Analytics**: View live Plotly governance charts, severity donut breakdowns, emotion signals, and detection rate metrics.

### 👤 Regular User Account Access
- **Sign In / Registration**: Enter any Username, Email, and Password on the initial sign-in screen.
- **Capabilities**:
  - Post messages to the real-time chat feed.
  - Inspect policy warnings on reported messages.
  - **`🚩 Report`** button to flag toxic content to the Admin queue without duplicate message posting.
  - Submit account ban appeals if restricted or muted by policy enforcement.

---

## 🧪 Running Tests

All tests use **in-memory SQLite** — no live Supabase connection or API keys required.

```bash
# Run the full test suite
python tests/run_all_tests.py

# Or run specific test modules with pytest
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
Cyber-Guard_AI/
├── app.py                      ← Thin Streamlit router (option-menu nav)
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
├── src/
│   ├── config.py               ← Constants, paths, severity levels, config resolution
│   ├── db.py                   ← SQLAlchemy ORM + dual-backend persistence
│   ├── pipeline.py             ← 8-step detection pipeline & existing msg reporting
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
│   ├── examples/               ← Cyberbullying precedent corpus (example_bank.csv)
│   └── policy_docs/            ← PECA 2016 / FIA policy snippets (policy_corpus.csv)
└── tests/
    ├── test_appeals.py         ← Appeal workflow tests
    ├── test_db_sqlalchemy.py   ← ORM persistence tests
    ├── test_pipeline.py        ← Pipeline tests
    ├── test_policy.py          ← Policy engine tests
    └── ...
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `users` | Identity registry (`user_id`, `username`, `email`, `role`, `status`, `created_at`) |
| `messages` | Every sent message with toxicity/emotion scores (`message_id`, `user_id`, `text`, `is_flagged`) |
| `verdicts` | LLM verdict per flagged message (`category`, `severity`, `user_report`, `admin_status`) |
| `actions` | Immutable audit log of all system/admin actions (`action_id`, `action_type`, `taken_by`) |
| `restricted_users` | Active block/mute records with `mute_expires_at` for 30-min auto-expiry |
| `appeals` | User-submitted appeal records with admin resolution (`appeal_id`, `appeal_text`, `status`) |

---

## ⚖️ Legal Notice

This system references Pakistan's **Prevention of Electronic Crimes Act (PECA) 2016** and **FIA Cyber Crime Wing** policy corpus for educational and research purposes only. It is not a substitute for professional legal advice.

- [Prevention of Electronic Crimes Act (PECA) 2016 - National Assembly of Pakistan](https://pakistancode.gov.pk/pdffiles/administrator6a061efe0ed5bd153fa8b79b8eb4cba7.pdf)
- [FIA Cyber Crime Wing Guidelines & Publications](https://www.fia.gov.pk/files/publications/860464251.pdf)

---

## 📝 License

Distributed under the MIT License — See [LICENSE](LICENSE) file for details.
