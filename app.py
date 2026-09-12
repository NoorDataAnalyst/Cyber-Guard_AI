"""
CyberGuard AI — Streamlit Application Entry Point (Thin Router).

All rendering logic lives in src/ui/* modules.
This file only configures the page, applies global styles, and routes tabs.
"""

import streamlit as st
from streamlit_option_menu import option_menu

# ── Page Config (MUST be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="CyberGuard AI | Cyberbullying Detection & RAG Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global Stylesheet ──────────────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Dark canvas */
    .stApp {
        background: #0b0d14;
    }
    .main > .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    /* Remove default Streamlit header padding */
    .stAppHeader {
        background: rgba(11, 13, 20, 0.9);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #1e2233;
    }

    /* Option menu navbar styling */
    .nav-link {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        transition: background 0.2s ease !important;
    }
    .nav-link-selected {
        background: linear-gradient(135deg, #5865f2, #7c3aed) !important;
        box-shadow: 0 4px 15px rgba(88, 101, 242, 0.35) !important;
    }

    /* Global badge styles (shared across tabs) */
    .badge-none     { background-color:#2e7d32; color:white; padding:3px 10px; border-radius:12px; font-weight:600; font-size:0.83rem; }
    .badge-mild     { background-color:#f57f17; color:white; padding:3px 10px; border-radius:12px; font-weight:600; font-size:0.83rem; }
    .badge-moderate { background-color:#e65100; color:white; padding:3px 10px; border-radius:12px; font-weight:600; font-size:0.83rem; }
    .badge-severe   { background-color:#c62828; color:white; padding:3px 10px; border-radius:12px; font-weight:600; font-size:0.83rem; }

    /* Card box */
    .card-box {
        background: #1e222d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        border: 1px solid #2d3241;
    }
    .legal-box {
        background-color: #1a2332;
        border-left: 4px solid #0288d1;
        padding: 12px 15px;
        border-radius: 4px;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    .restriction-banner {
        background-color: #3e1212;
        border: 1px solid #b71c1c;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        color: #ffcdd2;
    }
    .mute-banner {
        background-color: #332606;
        border: 1px solid #f57f17;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        color: #ffe0b2;
    }

    /* Streamlit widget overrides for dark theme harmony */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #1a1e2b !important;
        border: 1px solid #2d3241 !important;
        color: #e8eaf6 !important;
        border-radius: 8px !important;
    }
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(88,101,242,0.3);
    }

    /* Chat message styling */
    .stChatMessage {
        background: #1e222d !important;
        border: 1px solid #2d3241 !important;
        border-radius: 12px !important;
    }

    /* Sidebar collapse button */
    [data-testid="collapsedControl"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)


# ── Hero Header ────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align:center; padding: 8px 0 24px 0;">
        <div style="font-size:2.6rem; font-weight:900;
                    background:linear-gradient(135deg,#5865f2,#eb4b8b,#f5a623);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    letter-spacing:-1px; line-height:1.1;">
            🛡️ CyberGuard AI
        </div>
        <div style="color:#6b7280; font-size:0.97rem; margin-top:8px; font-weight:500;">
            Context-Aware Cyberbullying Detection with RAG Reasoning &amp; Policy Governance
        </div>
    </div>
""", unsafe_allow_html=True)


# ── Top Navigation (option-menu) ───────────────────────────────────────────
selected_tab = option_menu(
    menu_title=None,
    options=["Home", "Analytics", "Features", "Tech Stack", "Team", "About"],
    icons=["house-fill", "bar-chart-fill", "lightning-charge-fill", "cpu-fill", "people-fill", "info-circle-fill"],
    menu_icon="shield-fill",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "6px 12px",
            "background-color": "#141720",
            "border-radius": "14px",
            "border": "1px solid #2d3241",
            "margin-bottom": "24px",
        },
        "icon": {"color": "#8b9cf7", "font-size": "16px"},
        "nav-link": {
            "font-size": "0.88rem",
            "font-weight": "600",
            "color": "#9ea7c9",
            "border-radius": "8px",
            "--hover-color": "#1e222d",
        },
        "nav-link-selected": {
            "background": "linear-gradient(135deg, #5865f2, #7c3aed)",
            "color": "white",
            "box-shadow": "0 4px 15px rgba(88,101,242,0.35)",
        },
    },
    key="main_nav",
)


# ── Route to Tabs ─────────────────────────────────────────────────────────
if selected_tab == "Home":
    from src.ui.home import render_home_tab
    render_home_tab()

elif selected_tab == "Analytics":
    from src.ui.stats import render_stats_tab
    render_stats_tab()

elif selected_tab == "Features":
    from src.ui.features import render_features_tab
    render_features_tab()

elif selected_tab == "Tech Stack":
    from src.ui.tech_stack import render_tech_stack_tab
    render_tech_stack_tab()

elif selected_tab == "Team":
    from src.ui.team import render_team_tab
    render_team_tab()

elif selected_tab == "About":
    from src.ui.about import render_about_tab
    render_about_tab()
