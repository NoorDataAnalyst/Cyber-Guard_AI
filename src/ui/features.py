"""
Features Tab Module: Capabilities that exist in the running app.
"""

import streamlit as st


def render_features_tab():
    st.title("✨ Key Features & Capabilities")
    st.caption("What CyberGuard AI actually does — grounded in the implemented pipeline")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h4>Context-Aware Detection</h4>
            <p>Evaluates flagged messages alongside the surrounding conversation thread history,
            catching sarcastic insults and indirect harassment that isolated keyword filters miss.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎭</div>
            <h4>Emotion-Aware Signal Layer</h4>
            <p>Uses <code>SamLowe/roberta-base-go_emotions</code> to detect the dominant emotion
            (e.g. anger, disgust) alongside the <code>unitary/toxic-bert</code> toxicity score,
            giving the LLM richer signals to reason with.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📚</div>
            <h4>3-Index FAISS RAG Retrieval</h4>
            <p>Three FAISS CPU vector indices retrieve grounded evidence for every flagged message:
            thread history context, a curated precedent example bank, and legal/policy snippets
            from PECA 2016 and the FIA Cybercrime Wing.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🚩</div>
            <h4>Dual Reporting Pathways</h4>
            <p>Every message is scanned automatically by the signal layer. In addition, any chat
            participant can manually 🚩 Report a message, which forces it through the full
            RAG + LLM pipeline regardless of its toxicity score.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚖️</div>
            <h4>Deterministic Policy Engine</h4>
            <p>Severity scores from the LLM verdict are mapped to exact system actions:
            no action (clean), soft warning (mild), 30-minute mute (moderate), or full
            account block (severe) — with no probabilistic side-effects.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <h4>Appeal Workflow & Admin Governance</h4>
            <p>Blocked users can submit a written appeal directly from the Live Feed.
            30-minute mutes auto-expire. Admin moderators can approve or reject appeals,
            force-block/unblock users, and dismiss false positive flags from the
            Admin Governance Dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
