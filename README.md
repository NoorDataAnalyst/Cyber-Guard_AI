# 🛡️ Cyberbullying Detection & Governance System

A context-aware, emotion-aware, retrieval-augmented reasoning (RAG) cyberbullying detection and classification platform built with Python, HuggingFace transformers, FAISS vector search, Claude LLM reasoning, deterministic policy engine, and Streamlit.

---

## 🌟 Key Features

1. **Context-Aware Reasoning**: Analyzes flagged messages in the context of preceding conversation history thread, catching subtle and indirect bullying that single-message filters miss.
2. **Emotion Signal Layer**: Incorporates fine-grained emotion signals (`SamLowe/roberta-base-go_emotions`) alongside multi-label toxicity probabilities (`unitary/toxic-bert`) to inform the reasoning stage.
3. **Retrieval-Augmented Generation (FAISS RAG)**:
   - **Conversation Thread Context Index**: Retrieves last $N$ messages from active thread.
   - **Precedent Example Bank Index**: Retrieves top-k semantically similar labeled precedent examples from curated example bank.
   - **Legal & Policy Corpus Index**: Retrieves verified legal provisions (e.g. **Pakistan PECA 2016** Sections 20, 21, 24, and **FIA Cybercrime Wing** guidelines) to ground user-facing reports.
4. **Dual Reporting Pathways**:
   - **Automatic Detection**: Signal layer scans incoming chat messages in real time.
   - **Manual User Report**: Chat feed provides a direct 🚩 **Report Message** button allowing users to flag suspicious/sarcastic content.
5. **Dual Action Enforcement Mechanisms**:
   - **Automated Tool Restrictions**: Policy engine enforces soft warnings, conversation mutes, or message blocks based on severity.
   - **Admin Manual Authority**: Admin Dashboard enables human moderators to inspect full RAG context, view internal explanations, and manually **Block User**, **Unblock User**, **Override Severity**, or **Dismiss Flags**.
6. **No Scratch Model Training**: Uses public open-weights models for inference only. Nuanced classification is handled by a single LLM reasoning agent.

---

## 🏗️ Sequential Architecture

```
[ Incoming Message / Manual User Report ]
                   │
                   ▼
  [ SIGNAL LAYER (Fast Pretrained ML Inference) ]
    ├─ Toxicity Classifier (unitary/toxic-bert)
    └─ Emotion Classifier  (SamLowe/roberta-base-go_emotions)
                   │
                   ▼
       [ FLAG DECISION GATE ]
         ├─ If Clean  ──> Log as clean & stop
         └─ If Flagged ─> Proceed to RAG
                   │
                   ▼
   [ RETRIEVAL LAYER (3 FAISS CPU Vector Indices) ]
    ├─ (a) Thread Context History
    ├─ (b) Precedent Example Bank (data/examples/example_bank.csv)
    └─ (c) Legal & Policy Corpus  (data/policy_docs/policy_corpus.csv)
                   │
                   ▼
       [ LLM REASONING AGENT ] (Claude / Gemini API)
         └─ Strict JSON Output: {is_true_positive, category, severity, confidence, explanation}
                   │
                   ▼
       [ DETERMINISTIC POLICY ENGINE ]
         └─ Severity -> Action Mapping (none, soft warning, mute sender, block message)
                   │
                   ▼
       [ USER-FACING REPORT GENERATOR ] (Only for warn/mute/block)
         └─ Cites retrieved PECA 2016 / FIA Pakistan legal snippets + Legal Disclaimer
                   │
                   ▼
   [ SQLite LOGGING & STREAMLIT DUAL-VIEW INTERFACE ]
    ├─ 💬 Live Chat Feed (with manual 🚩 Report buttons & explanation drawers)
    └─ 📊 Admin Governance Dashboard (with RAG inspection & manual overrides)
```

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- Python 3.10 or 3.11
- Pip package manager

### 2. Installation
```bash
# Clone or navigate to the project directory
cd cyberbullying-detector

# Create and activate virtual environment (optional)
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and add your API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Optional Gemini fallback
GEMINI_API_KEY=your_gemini_api_key_here
```
*Note: If no API key is provided, the system seamlessly uses its built-in grounded rule-based reasoning engine without crashing.*

### 4. Running the Streamlit Application
```bash
streamlit run app.py
```

### 5. Running the Unit Test Suite
```bash
python tests/run_all_tests.py
```

---

## 📊 Evaluation & Benchmark Results

We evaluated the pretrained `unitary/toxic-bert` model against a classical ML baseline (**TF-IDF + Logistic Regression**) trained from scratch on a held-out test split of the Kaggle Jigsaw Toxic Comment dataset (`data/raw/jigsaw_test_sample.csv`).

| Model / Classifier | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **Classical ML Baseline (TF-IDF + Logistic Reg)** | 0.8800 | 0.7333 | 0.8000 |
| **Pretrained Transformer (`unitary/toxic-bert`)** | **0.9375** | **0.9375** | **0.9375** |

- **Takeaway**: The off-the-shelf pretrained transformer (`toxic-bert`) significantly outperforms the classical TF-IDF baseline in both recall and F1-score without requiring custom training.

---

## ⚖️ Business Logic: Severity $\rightarrow$ Action Rules

| Severity Level | Automated System Action | Admin Authority Options |
| :--- | :--- | :--- |
| **none** | Logged as clean message | Admin can manually flag if reported by user |
| **mild** | Soft in-app warning shown to sender | Admin can escalate severity or dismiss flag |
| **moderate** | Mute sender in thread + flag for admin review | Admin can force block user, unblock, or adjust severity |
| **severe** | Escalate immediately + block message | Admin can unblock message, override verdict, or confirm permanent block |

---

## ⚠️ Known Limitations & Privacy Considerations

1. **Demographic & Dialect Bias in Public Toxicity Models**:
   - Toxicity classifiers trained on public datasets like Kaggle Jigsaw have documented false-positive bias against certain dialects, colloquial slang, and reclaimed language. The secondary LLM reasoning agent and RAG context retrieval step serve specifically to mitigate this single-classifier bias.
2. **Data Retention & Privacy Compliance**:
   - The current SQLite implementation logs messages and verdicts locally for auditability. A production deployment must implement automatic data retention/deletion schedules (e.g. 30-day auto-purge) to comply with GDPR and local privacy regulations.
3. **Legal Information Disclaimer**:
   - All generated user reports carry an explicit notice stating that citations from **Pakistan PECA 2016** or platform guidelines are provided for general educational and policy awareness purposes only, and do not constitute formal legal advice.
