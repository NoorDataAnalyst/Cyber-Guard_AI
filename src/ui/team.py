"""
Team Tab Module: Project contributors.
"""

import streamlit as st


TEAM_MEMBERS = [
    {"name": "Hira Saleem",        "avatar": "👩‍💻"},
    {"name": "Muhammad Usman",     "avatar": "👨‍💻"},
    {"name": "Peer Talha Dawood",  "avatar": "👨‍💻"},
    {"name": "Shumail Iqbal",      "avatar": "👨‍💻"},
    {"name": "Noor ul Ain Zahid",  "avatar": "👩‍💻"},
    {"name": "Zeeshan",            "avatar": "👨‍💻"},
]


def render_team_tab():
    st.markdown("""
        <style>
        .team-card {
            background: linear-gradient(135deg, #1e222d 0%, #252a37 100%);
            border: 1px solid #2d3241;
            border-radius: 14px;
            padding: 28px 24px;
            margin-bottom: 18px;
            text-align: center;
            transition: border-color 0.2s ease;
        }
        .team-card:hover {
            border-color: #5865f2;
        }
        .team-avatar {
            font-size: 2.8rem;
            display: block;
            margin-bottom: 12px;
        }
        .team-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #e8eaf6;
            margin: 0;
        }
        .section-header {
            text-align: center;
            margin-bottom: 36px;
        }
        .section-header h2 {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #5865f2, #8b9cf7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .section-header p {
            color: #6b7280;
            font-size: 1rem;
            margin-top: 8px;
        }
        .ack-box {
            background: linear-gradient(135deg, #1a2036, #1e2a45);
            border: 1px solid #2d3a5a;
            border-radius: 12px;
            padding: 24px 30px;
            margin-top: 32px;
        }
        .ack-box h4 { color: #8b9cf7; margin-top: 0; }
        .ack-box ul  { color: #9ea7c9; line-height: 2; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="section-header">
            <h2>👥 Meet the Team</h2>
            <p>CyberGuard AI was designed and built by a team of six.</p>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, member in enumerate(TEAM_MEMBERS):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="team-card">
                    <span class="team-avatar">{member['avatar']}</span>
                    <p class="team-name">{member['name']}</p>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("""
        <div class="ack-box">
            <h4>🙏 Acknowledgements</h4>
            <ul>
                <li><b>HuggingFace</b> — <code>unitary/toxic-bert</code> and <code>SamLowe/roberta-base-go_emotions</code> pretrained models</li>
                <li><b>Sentence-Transformers</b> — <code>all-MiniLM-L6-v2</code> dense embeddings for RAG retrieval</li>
                <li><b>Meta AI / Facebook</b> — FAISS CPU vector index library</li>
                <li><b>Anthropic</b> — Claude API for LLM reasoning</li>
                <li><b>Google DeepMind</b> — Gemini API as LLM fallback</li>
                <li><b>Supabase</b> — Managed Postgres backend for production persistence</li>
                <li><b>Prevention of Electronic Crimes Act (PECA) 2016</b> — Pakistan's primary cybercrime legal corpus</li>
                <li><b>Federal Investigation Agency (FIA)</b> — Pakistan Cyber Crime Wing policy references</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
