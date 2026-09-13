# 🛡️ CyberGuard AI — Cyberbullying Detection & RAG Governance Platform

> Real-time contextual cyberbullying detection, transparent decision governance, and automated multi-tier policy enforcement powered by signal models, 3-index FAISS RAG, and LLM reasoning.

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

## 📸 Key Features & System Overview

| Feature | Details |
|---|---|
| **Real-Time Live Chat Feed** | 2-second auto-updating live chat stream powered by `@st.fragment` without full page reloads. |
| **Multi-Signal Classifier** | `unitary/toxic-bert` for multi-label toxicity + `SamLowe/roberta-base-go_emotions` for emotional intent detection. |
| **3-Index FAISS RAG** | Dense vector search (`all-MiniLM-L6-v2`) retrieving thread context, precedent dataset examples, and PECA 2016 legal policies. |
| **LLM Reasoning Agent** | Grounded decision generation via Google Gemini Flash / Anthropic Claude API with network exception fallback. |
| **Multi-Tier Policy Enforcement** | Automated enforcement rules mapping severity levels (Clean → None, Mild → Soft Warning, Moderate → 30-min Mute, Severe → Block Message & Account Suspension). |
| **Admin Governance & Appeals** | Centralized admin queue to review account ban appeals, audit flagged verdicts, and execute manual block/unblock overrides. |
| **Analytics Dashboard** | Embedded Plotly analytics charts featuring severity donut distribution, category breakdown, detection rate gauge, and raw metrics table. |
| **Dual-Backend Database** | Production-ready SQLAlchemy ORM supporting Supabase Postgres with automatic SQLite local fallback. |
| **Responsive UI Design** | Modern glassmorphism UI featuring desktop top horizontal navigation, mobile slide-out sidebar (`☰`), and single-layer round pill chat input. |

---

## 🏗️ 8-Step Pipeline Architecture

```
[ User Input Message ]
          │
          ▼
   1. Preprocessing & Text Normalization
          │
          ▼
   2. Restriction Pre-Check (Active Mute / Ban Expiry Audit)
          │
          ▼
   3. Dual Model Signal Scoring (toxic-bert + roberta-go-emotions)
          │
          ▼
   4. 3-Index FAISS RAG Retrieval (Context + Precedents + Legal Policies)
          │
          ▼
   5. LLM Agent Reasoning & Structured Verdict Generation
          │
          ▼
   6. Policy Engine Action Enforcement (Soft Warning / 30-min Mute / Account Suspension)
          │
          ▼
   7. Database Persistence & Audit Action Logging
          │
          ▼
   8. Real-Time Chat Feed Render & Policy Notice Dispatch
```

---

## 🚀 Quickstart (Local Development)

### 1. Clone the repository & create virtual environment

```bash
git clone https://github.com/ihirasaleem/Cyber-Guard_AI.git
cd Cyber-Guard_AI

python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

**Environment Variables Configuration (`.env`):**

| Key | Description | Default / Example |
|---|---|---|
| `LLM_PROVIDER` | LLM model vendor | `gemini` or `anthropic` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | `sk-ant-...` |
| `DATABASE_URL` | *(Optional)* Supabase Postgres URI | `postgresql://user:pass@db.ref.supabase.co:5432/postgres` |

### 4. Launch the application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🗄️ Database Schema

SQLAlchemy ORM automatically initializes database tables on startup for both Postgres and SQLite:

| Table Name | Description |
|---|---|
| `users` | User identity registry (`user_id`, `username`, `email`, `role`, `created_at`) |
| `messages` | Historical message log with toxicity & emotion scores (`message_id`, `sender`, `text`, `is_flagged`) |
| `verdicts` | Detailed AI evaluation outputs (`verdict_id`, `category`, `severity`, `user_report`, `admin_status`) |
| `actions` | Immutable audit log of all system & administrator override actions |
| `restricted_users` | Active user account restrictions (`restriction_id`, `status`, `mute_expires_at`, `reason`) |
| `appeals` | Account ban appeal submissions and admin review decisions |

---

## 🧪 Running Automated Tests

Run the complete pytest test suite (uses isolated in-memory SQLite database):

```bash
.\venv\Scripts\pytest.exe -v
```

All **63 unit tests** verify ORM persistence, appeal workflows, RAG retrieval accuracy, emotion classifiers, policy rules, and pipeline execution.

---

## ⚖️ Legal & Policy Corpus References

This project incorporates policy guidelines and legal definitions from Pakistan's primary cybercrime legislation:
- **Prevention of Electronic Crimes Act (PECA) 2016** — National Assembly of Pakistan
- **Federal Investigation Agency (FIA) Cyber Crime Wing Guidelines**

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
