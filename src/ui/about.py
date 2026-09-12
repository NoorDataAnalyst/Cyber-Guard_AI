"""
About Tab Module: System overview, actual 8-step pipeline description, and workflow diagram.
"""

import streamlit as st


def render_about_tab():
    st.title("📖 About CyberGuard AI")
    st.caption("A Context & Emotion-Aware RAG Cyberbullying Detection and Governance System")

    st.markdown("""
    ### 🎯 Project Overview
    Traditional toxicity filters evaluate messages in isolation using simple keyword blacklists.
    This approach frequently fails when encountering **sarcastic insults**, **passive-aggressive
    exclusion**, or **context-dependent harassment**.

    **CyberGuard AI** is a cyberbullying detection and governance platform that combines a
    fast neural signal layer with retrieval-augmented LLM reasoning and a deterministic policy
    engine — providing transparent, auditable verdicts to both restricted users and admin moderators.

    ---

    ### ⚙️ How the Pipeline Works (8 Steps)

    1. **Pre-Check: Restriction Gate**
       Before any analysis, the pipeline checks if the sender is currently **blocked or muted**.
       If so, the message is rejected immediately and no classifiers are invoked.

    2. **Message Save**
       The raw message is persisted to the database with sender identity via `save_message()`.

    3. **Signal Layer — Toxicity Classifier**
       `unitary/toxic-bert` scores the cleaned message text and returns a toxicity probability.

    4. **Signal Layer — Emotion Classifier**
       `SamLowe/roberta-base-go_emotions` identifies the dominant emotion label and its confidence.

    5. **Flag Decision Gate**
       If the toxicity score exceeds the threshold (default: 0.50) **or** the message was
       manually reported by a user (🚩 Report), the message is flagged and passes to the
       RAG retrieval layer. Clean messages below threshold are logged and no further LLM
       processing occurs.

    6. **Retrieval-Augmented Generation (3-Index FAISS)**
       Three separate FAISS CPU vector indices are queried:
       - **(a) Thread History Context** — last N messages from the conversation
       - **(b) Precedent Example Bank** — top-k semantically similar labeled cyberbullying examples
       - **(c) Legal & Policy Corpus** — Pakistan PECA 2016 (Sections 20, 21, 24) and FIA Cybercrime Wing snippets

    7. **LLM Reasoning Agent**
       Anthropic Claude (with Gemini as fallback) receives the flagged message, signal scores,
       retrieved context, precedent examples, and policy snippets. It returns a structured
       JSON verdict containing: `is_true_positive`, `category`, `severity`, `confidence`,
       `explanation`, and a `user_report` policy notice.

    8. **Policy Engine → Action + Logging**
       The deterministic policy engine maps severity to a system action:
       - **None / not_bullying**: No action taken — logged as clean.
       - **Mild**: Soft in-app warning recorded in the audit log.
       - **Moderate**: Sender muted for **30 minutes** (auto-expires; sending disabled, viewing allowed).
       - **Severe**: Sender account **blocked** — user can submit an appeal via the Live Feed for Admin review.

       All actions are written to the `actions` audit table and the verdict is saved to `verdicts`.
       The Admin Governance Dashboard surfaces all flagged verdicts with full RAG context for
       human moderator review and manual override.
    """)

    st.markdown("---")
    st.markdown("### 🔄 Pipeline Workflow Diagram")
    st.caption("End-to-end flow of every message processed by CyberGuard AI")

    st.graphviz_chart("""
    digraph CyberGuardPipeline {
        rankdir=TB;
        node [
            shape=box,
            style="rounded,filled",
            fontname="Helvetica",
            fontsize=12,
            margin="0.25,0.12"
        ];
        edge [fontsize=10, fontname="Helvetica"];

        // ── Nodes ─────────────────────────────────────────────────
        Message     [label="📨  New Message\\n(sender + text)",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#5865f2"];

        PreCheck    [label="🔒  Restriction Pre-Check\\n(blocked / muted?)",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#f5a623",
                      shape=diamond];

        Rejected    [label="🚫  Message Rejected\\n(account restricted)",
                      fillcolor="#3e1212", fontcolor="#ffcdd2", color="#c62828"];

        SignalLayer [label="⚡  Signal Layer\\ntoxic-bert  +  roberta-go_emotions",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#5865f2"];

        FlagGate    [label="🚦  Flag Decision Gate\\ntoxicity score ≥ 0.50\\nor manual report?",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#f5a623",
                      shape=diamond];

        Logged      [label="✅  Logged Clean\\n(no further processing)",
                      fillcolor="#1b3324", fontcolor="#c8e6c9", color="#43a047"];

        Retrieval   [label="📚  3-Index FAISS Retrieval\\n(a) Thread Context\\n(b) Precedent Examples\\n(c) PECA 2016 / FIA Policy",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#5865f2"];

        LLMAgent    [label="🤖  LLM Reasoning Agent\\nAnthropic Claude  (Gemini fallback)\\n→ JSON verdict",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#8b9cf7"];

        PolicyEng   [label="⚖️  Policy Engine\\nSeverity → Action",
                      fillcolor="#1a1e2b", fontcolor="#e8eaf6", color="#5865f2"];

        ActWarn     [label="🟡  Mild\\nSoft Warning\\n(logged)",
                      fillcolor="#332606", fontcolor="#ffe0b2", color="#f57f17"];

        ActMute     [label="🟠  Moderate\\nMute 30 min\\n(auto-expires)",
                      fillcolor="#2d1a00", fontcolor="#ffcc80", color="#e65100"];

        ActBlock    [label="🔴  Severe\\nAccount Blocked\\n+ Appeal Queue",
                      fillcolor="#3e1212", fontcolor="#ffcdd2", color="#c62828"];

        Admin       [label="🛡️  Admin Dashboard\\nAudit · Override · Approve Appeal",
                      fillcolor="#1a1e2b", fontcolor="#8b9cf7", color="#5865f2"];

        // ── Edges ─────────────────────────────────────────────────
        Message     -> PreCheck;
        PreCheck    -> Rejected  [label=" yes (restricted)"];
        PreCheck    -> SignalLayer [label=" no (active)"];
        SignalLayer -> FlagGate;
        FlagGate    -> Logged    [label=" below threshold"];
        FlagGate    -> Retrieval [label=" flagged / reported"];
        Retrieval   -> LLMAgent;
        LLMAgent    -> PolicyEng;
        PolicyEng   -> ActWarn   [label=" mild"];
        PolicyEng   -> ActMute   [label=" moderate"];
        PolicyEng   -> ActBlock  [label=" severe"];
        ActWarn     -> Admin;
        ActMute     -> Admin;
        ActBlock    -> Admin;
    }
    """)

    st.markdown("---")
    st.markdown("""
    <div style="background:#1a2332; border-left:4px solid #0288d1; padding:12px 15px;
                border-radius:4px; font-size:0.88rem; color:#9ea7c9;">
    <b>Legal Notice</b>: This system references Pakistan's Prevention of Electronic Crimes Act
    (PECA) 2016 and FIA Cyber Crime Wing policy corpus for educational and research purposes
    only. It does not constitute formal legal advice.
    </div>
    """, unsafe_allow_html=True)
