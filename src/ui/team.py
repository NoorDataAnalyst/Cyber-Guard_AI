"""
Team Tab Module: Project contributors.
"""

import streamlit as st


TEAM_MEMBERS = [
    {
        "name": "Hira Saleem",
        "avatar": "👩‍💻",
        "linkedin": "https://www.linkedin.com/in/hira-saleem-595496180/"
    },
    {
        "name": "Muhammad Usman",
        "avatar": "👨‍💻",
        "linkedin": "https://www.linkedin.com/in/iusman07/"
    },
    {
        "name": "Peer Talha Dawood",
        "avatar": "👨‍💻",
        "linkedin": "https://www.linkedin.com/in/peer-talha-khan-2b1911228/"
    },
    {
        "name": "Shumail Iqbal",
        "avatar": "👨‍💻",
        "linkedin": "https://www.linkedin.com/in/shumail-iqbal-4ab23b431/"
    },
    {
        "name": "Noor ul Ain Zahid",
        "avatar": "👩‍💻",
        "linkedin": "https://www.linkedin.com/in/noor-ul-ain-zahid-588895341/"
    },
    {
        "name": "Zeeshan Ahmad",
        "avatar": "👨‍💻",
        "linkedin": "https://www.linkedin.com/in/zeeshier/"
    },
]


def render_team_tab():
    # Shared styles (.team-card, .section-header, .ack-box) live globally in app.py.
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
                    <a href="{member['linkedin']}" target="_blank" class="team-linkedin-btn">
                        <svg style="width: 14px; height: 14px; fill: currentColor; vertical-align: text-bottom; margin-right: 4px;" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>
                        LinkedIn Profile
                    </a>
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
