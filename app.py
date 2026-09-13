"""
CyberGuard AI — Streamlit Application Entry Point (Thin Router).

All rendering logic lives in src/ui/* modules.
This file only configures the page, applies the global design system
(colors, spacing, responsive rules), and routes tabs.
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

# ── State Initialization for Theme & Navigation ────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

is_dark = (st.session_state["theme"] == "dark")

# ── Dynamic CSS Design System (Light & Dark Mode) ───────────────────────────
bg_val           = "#0B0F19" if is_dark else "#F8FAFC"
surface_val      = "#151D2A" if is_dark else "#FFFFFF"
surface_alt_val  = "#1E293B" if is_dark else "#F1F5F9"
border_val       = "#263346" if is_dark else "#E2E8F0"
border_hover_val = "#3B82F6" if is_dark else "#CBD5E1"
text_val         = "#F8FAFC" if is_dark else "#0F172A"
text_muted_val   = "#94A3B8" if is_dark else "#475569"
text_faint_val   = "#64748B" if is_dark else "#94A3B8"

primary_val      = "#3B82F6" if is_dark else "#2563EB"
primary_dark_val = "#2563EB" if is_dark else "#1D4ED8"
primary_soft_val = "rgba(59, 130, 246, 0.18)" if is_dark else "#EFF6FF"

nav_bg           = "#151D2A" if is_dark else "#FFFFFF"
nav_link_color   = "#94A3B8" if is_dark else "#475569"
nav_hover_bg     = "#1E293B" if is_dark else "#F1F5F9"

# Dynamic status badge colors tailored for dark/light mode
success_val        = "#34D399" if is_dark else "#059669"
success_bg_val     = "rgba(5, 150, 105, 0.22)" if is_dark else "#ECFDF5"
success_border_val = "rgba(52, 211, 153, 0.4)" if is_dark else "#A7F3D0"

warning_val        = "#FBBF24" if is_dark else "#D97706"
warning_bg_val     = "rgba(217, 119, 6, 0.22)" if is_dark else "#FFFBEB"
warning_border_val = "rgba(251, 191, 36, 0.4)" if is_dark else "#FDE68A"

orange_val         = "#FB923C" if is_dark else "#EA580C"
orange_bg_val      = "rgba(234, 88, 12, 0.22)" if is_dark else "#FFEDD5"
orange_border_val  = "rgba(251, 146, 60, 0.4)" if is_dark else "#FDBA74"

danger_val         = "#F87171" if is_dark else "#DC2626"
danger_bg_val      = "rgba(220, 38, 38, 0.22)" if is_dark else "#FEF2F2"
danger_border_val  = "rgba(248, 113, 113, 0.4)" if is_dark else "#FCA5A5"

info_val           = "#60A5FA" if is_dark else "#2563EB"
info_bg_val        = "rgba(37, 99, 235, 0.22)" if is_dark else "#EFF6FF"
info_border_val    = "rgba(96, 165, 250, 0.4)" if is_dark else "#BFDBFE"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --bg: {bg_val};
        --surface: {surface_val};
        --surface-alt: {surface_alt_val};
        --border: {border_val};
        --border-hover: {border_hover_val};
        --text: {text_val};
        --text-muted: {text_muted_val};
        --text-faint: {text_faint_val};

        --primary: {primary_val};
        --primary-dark: {primary_dark_val};
        --primary-soft: {primary_soft_val};
        --accent: #06B6D4;
        --teal: #0D9488;

        --success: {success_val};   --success-bg: {success_bg_val};  --success-border: {success_border_val};
        --warning: {warning_val};   --warning-bg: {warning_bg_val};  --warning-border: {warning_border_val};
        --orange:  {orange_val};    --orange-bg:  {orange_bg_val};   --orange-border:  {orange_border_val};
        --danger:  {danger_val};    --danger-bg:  {danger_bg_val};   --danger-border:  {danger_border_val};
        --info:    {info_val};      --info-bg:    {info_bg_val};     --info-border:    {info_border_val};

        --radius-sm: 10px;
        --radius: 16px;
        --radius-lg: 24px;
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.2);
        --shadow: 0 4px 20px -4px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 12px 32px -8px rgba(0, 0, 0, 0.4);
        --shadow-glow: 0 0 25px rgba(37, 99, 235, 0.2);
    }}

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    html {{
        color-scheme: {"dark" if is_dark else "light"} only;
    }}

    /* ── Base canvas & Full-Screen Dark Coverage ─────────────────────── */
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    section.main,
    footer {{
        background-color: var(--bg) !important;
        background: var(--bg) !important;
        color: var(--text) !important;
    }}

    /* Iframe & Component Transparent Backgrounds for Navbar */
    iframe,
    [data-testid="stCustomComponentV1"],
    [data-testid="stCustomComponentV1"] iframe,
    div[data-testid="stCustomComponentV1"] > iframe {{
        background-color: transparent !important;
        background: transparent !important;
    }}

    /* Radio Buttons & Form Controls Dark Mode Styling */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] p,
    div[data-testid="stRadio"] span,
    div[role="radiogroup"] label,
    div[role="radiogroup"] label span {{
        color: var(--text) !important;
    }}
    .main > .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }}
    p, li, span, label, h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span {{ color: var(--text) !important; }}
    .stCaption, [data-testid="stCaptionContainer"] {{ color: var(--text-muted) !important; font-weight: 500; }}

    .stAppHeader, header[data-testid="stHeader"] {{
        background: {"rgba(11, 15, 25, 0.95)" if is_dark else "rgba(248, 250, 252, 0.95)"} !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
    }}

    /* Sidebar Full Dark Mode Coverage */
    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarNav"] {{
        background-color: var(--surface) !important;
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }}

    /* Custom Scrollbars */
    ::-webkit-scrollbar {{ height: 6px; width: 6px; }}
    ::-webkit-scrollbar-thumb {{ background: {"#334155" if is_dark else "#CBD5E1"}; border-radius: 999px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {"#475569" if is_dark else "#94A3B8"}; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}

    /* ── Modern Hero Header ──────────────────────────────────────────── */
    .cg-hero {{ text-align: center; padding: 10px 0 26px 0; }}
    .cg-hero-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--primary-soft);
        color: var(--primary);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 14px;
    }}
    .cg-hero-title {{
        font-size: clamp(1.8rem, 4.5vw, 2.6rem);
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin: 0;
    }}
    .cg-hero-title .accent {{
        background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .cg-hero-sub {{
        color: var(--text-muted);
        font-size: clamp(0.88rem, 2vw, 1.02rem);
        margin-top: 10px;
        font-weight: 500;
        max-width: 660px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }}

    /* ── Top Navigation (streamlit-option-menu) ───────────────────────── */
    .nav-link {{
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 18px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
    }}
    .nav-link-selected {{
        background: #2563EB !important;
        color: white !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important;
    }}

    /* ── Modern Card Surface Components ────────────────────────────── */
    .card-box {{
        background: var(--surface) !important;
        border-radius: var(--radius);
        padding: 22px 24px;
        margin-bottom: 18px;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .card-box:hover {{
        border-color: var(--border-hover) !important;
        box-shadow: var(--shadow-md);
    }}
    .chart-card {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg);
        padding: 24px;
        margin-bottom: 22px;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .chart-card:hover {{
        box-shadow: var(--shadow-md);
    }}
    .feature-card {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius);
        padding: 24px;
        margin-bottom: 20px;
        height: 100%;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }}
    .feature-card:hover {{
        border-color: var(--primary) !important;
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    .feature-icon {{ font-size: 2rem; margin-bottom: 12px; }}
    .feature-card h4 {{ margin: 4px 0 8px 0; color: var(--text) !important; font-weight: 700; font-size: 1.1rem; }}
    .feature-card p {{ color: var(--text-muted) !important; font-size: 0.94rem; margin: 0; line-height: 1.6; }}

    .team-card {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg);
        padding: 28px 22px;
        margin-bottom: 18px;
        text-align: center;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }}
    .team-card:hover {{
        border-color: var(--primary) !important;
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    .team-avatar {{ font-size: 2.8rem; display: block; margin-bottom: 12px; }}
    .team-name {{ font-size: 1.05rem; font-weight: 700; color: var(--text) !important; margin: 0 0 10px 0; }}
    .team-linkedin-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-top: 6px;
        padding: 6px 14px;
        background: var(--primary-soft) !important;
        color: var(--primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }}
    .team-linkedin-btn:hover {{
        background: var(--primary) !important;
        color: white !important;
        border-color: var(--primary) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }}

    .section-header {{ text-align: center; margin-bottom: 32px; }}
    .section-header h2 {{
        font-size: clamp(1.5rem, 3.5vw, 1.9rem);
        font-weight: 800;
        color: var(--text) !important;
        letter-spacing: -0.02em;
        margin: 0;
    }}
    .section-header p {{ color: var(--text-muted) !important; font-size: 0.98rem; margin-top: 8px; }}

    .stats-header {{ text-align: center; margin-bottom: 30px; }}
    .stats-header h2 {{
        font-size: clamp(1.5rem, 3.5vw, 1.85rem);
        font-weight: 800;
        color: var(--text) !important;
        letter-spacing: -0.02em;
        margin: 0;
    }}
    .stats-header p {{ color: var(--text-muted) !important; font-size: 0.94rem; margin-top: 6px; }}

    .ack-box {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius);
        padding: 24px 28px;
        margin-top: 30px;
        box-shadow: var(--shadow);
    }}
    .ack-box h4 {{ color: var(--text) !important; font-weight: 700; margin-top: 0; font-size: 1.1rem; }}
    .ack-box ul {{ color: var(--text-muted) !important; line-height: 2; font-size: 0.94rem; }}
    .ack-box li b {{ color: var(--text) !important; }}

    /* ── Modern Status Badges (Pill Chips) ─────────────────────────── */
    .badge-none     {{ background: var(--success-bg) !important; color: var(--success) !important; border: 1px solid var(--success-border) !important; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.02em; display: inline-block; }}
    .badge-mild     {{ background: var(--warning-bg) !important; color: var(--warning) !important; border: 1px solid var(--warning-border) !important; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.02em; display: inline-block; }}
    .badge-moderate {{ background: var(--orange-bg)  !important; color: var(--orange)  !important; border: 1px solid var(--orange-border)  !important; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.02em; display: inline-block; }}
    .badge-severe   {{ background: var(--danger-bg)  !important; color: var(--danger)  !important; border: 1px solid var(--danger-border)  !important; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.02em; display: inline-block; }}

    /* ── Info & Warning Banners ─────────────────────────────────────── */
    .legal-box {{
        background: var(--info-bg);
        border-left: 4px solid var(--primary);
        padding: 14px 18px;
        border-radius: var(--radius-sm);
        font-size: 0.92rem;
        color: var(--text) !important;
        margin-top: 12px;
        line-height: 1.6;
    }}
    .restriction-banner {{
        background: var(--danger-bg);
        border: 1px solid var(--danger-border);
        border-radius: var(--radius);
        padding: 18px 22px;
        margin-bottom: 24px;
        color: var(--danger);
    }}
    .restriction-banner h4 {{ margin-top: 0; font-weight: 700; }}
    .mute-banner {{
        background: var(--warning-bg);
        border: 1px solid var(--warning-border);
        border-radius: var(--radius);
        padding: 18px 22px;
        margin-bottom: 24px;
        color: var(--warning);
    }}
    .mute-banner h4 {{ margin-top: 0; font-weight: 700; }}

    /* ── Inputs, Form Controls & Dropdown Popovers ───────────────────── */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] > div,
    .stSelectbox > div > div {{
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        caret-color: var(--primary) !important;
        -webkit-text-fill-color: var(--text) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"],
    li[role="option"] {{
        background-color: var(--surface) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
    }}
    li[role="option"]:hover {{
        background-color: var(--surface-alt) !important;
    }}
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="input"]:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }}
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: var(--text-faint) !important;
        -webkit-text-fill-color: var(--text-faint) !important;
        opacity: 1 !important;
    }}
    .stButton > button {{
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2) !important;
    }}
    .stButton > button:hover {{
        background: var(--primary-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important;
    }}

    /* ── Streamlit Tabs Styling ──────────────────────────────────────── */
    button[data-baseweb="tab"] {{
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 12px 20px !important;
        color: var(--text-muted) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom-color: var(--primary) !important;
    }}

    /* ── Single-Layer Clean Chat Feed Styling (Outer Layer Removed) ── */
    [data-testid="stChatMessage"],
    .stChatMessage {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        padding: 4px 0 !important;
        margin-bottom: 12px !important;
    }}

    /* The ONLY Message Card Box */
    [data-testid="stChatMessageContent"],
    .stChatMessageContent {{
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 16px 20px !important;
        margin: 0 !important;
        transition: border-color 0.15s ease !important;
    }}
    [data-testid="stChatMessageContent"]:hover {{
        border-color: var(--border-hover) !important;
    }}
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessageContent"] div {{
        color: var(--text) !important;
    }}

    /* Expander Inside Chat Messages (Clean Integrated Drawer) */
    [data-testid="stChatMessage"] [data-testid="stExpander"],
    [data-testid="stChatMessage"] details,
    [data-testid="stChatMessage"] summary {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }}
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 8px 0 0 0 !important;
    }}

    /* ── Single-Layer Chat Input (Outer Dock Transparent) ─────────────── */
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    .stBottomBlockContainer,
    .stBottomBlockContainer > div,
    [data-testid="stChatInput"] {{
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        backdrop-filter: none !important;
        filter: none !important;
        padding-bottom: 0.25rem !important;
        padding-top: 0.25rem !important;
    }}

    /* Beautiful Round Pill Border around Chat Input Field */
    div[data-testid="stChatInput"] > div,
    [data-testid="stChatInputContainer"] {{
        background-color: var(--surface) !important;
        background: var(--surface) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 28px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        padding: 6px 10px 6px 18px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    /* Hover & Focus Halo Effect */
    div[data-testid="stChatInput"] > div:hover,
    [data-testid="stChatInputContainer"]:hover {{
        border-color: var(--primary) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
    }}

    div[data-testid="stChatInput"] > div:focus-within,
    [data-testid="stChatInputContainer"]:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 6px 24px rgba(37, 99, 235, 0.3), 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }}

    /* Textarea Typography & Scrollbar */
    [data-testid="stChatInputTextArea"],
    div[data-testid="stChatInput"] textarea,
    [data-testid="stChatInputContainer"] textarea {{
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.96rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        caret-color: var(--primary) !important;
        padding: 6px 0 !important;
    }}

    [data-testid="stChatInputTextArea"]::placeholder,
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: var(--text-faint) !important;
        -webkit-text-fill-color: var(--text-faint) !important;
        font-size: 0.94rem !important;
        font-weight: 400 !important;
        opacity: 0.85 !important;
    }}

    /* Modern Circular Gradient Send Button */
    [data-testid="stChatInputSubmitButton"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    [data-testid="stChatInputSubmitButton"] button {{
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }}

    [data-testid="stChatInputSubmitButton"] button:hover {{
        transform: scale(1.08) translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
        background: linear-gradient(135deg, #1D4ED8 0%, #0891B2 100%) !important;
    }}

    [data-testid="stChatInputSubmitButton"] button:active {{
        transform: scale(0.96) !important;
    }}

    [data-testid="stChatInputSubmitButton"] button svg {{
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
        width: 18px !important;
        height: 18px !important;
    }}

    /* Expanders Dark Mode Coverage */
    [data-testid="stExpander"],
    details,
    summary,
    [data-testid="stExpanderDetails"] {{
        background-color: var(--surface) !important;
        background: var(--surface) !important;
        border-color: var(--border) !important;
        color: var(--text) !important;
        border-radius: var(--radius-sm) !important;
    }}

    /* Dataframes horizontal scroll */
    [data-testid="stDataFrame"] {{ overflow-x: auto; border-radius: var(--radius-sm); }}

    /* ── Responsive Rules (Desktop vs Mobile ☰ Hamburger) ────────────── */

    /* Desktop View (screens > 768px) */
    @media (min-width: 769px) {{
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
    }}

    /* Mobile View (screens <= 768px) */
    @media (max-width: 768px) {{
        /* Hide ONLY the top desktop horizontal navbar on mobile screens */
        div[data-testid="stElementContainer"]:has(#desktop-navbar-marker),
        div[data-testid="stElementContainer"]:has(#desktop-navbar-marker) + div[data-testid="stElementContainer"] {{
            display: none !important;
            height: 0px !important;
            min-height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        /* Show and position top-left ☰ three-bar line menu button */
        [data-testid="collapsedControl"] {{
            display: flex !important;
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            z-index: 999999 !important;
            background: {surface_val} !important;
            border: 1px solid {border_val} !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
            padding: 6px 10px !important;
        }}
        [data-testid="collapsedControl"] button {{
            color: {primary_val} !important;
        }}

        /* Mobile Sidebar Container & Hamburger Menu Tabs Styling */
        [data-testid="stSidebar"] {{
            background: {surface_val} !important;
            border-right: 1px solid {border_val} !important;
        }}
        [data-testid="stSidebar"] iframe,
        [data-testid="stSidebar"] [data-testid="stIframe"],
        [data-testid="stSidebar"] [data-testid="stCustomComponentV1"] {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            min-height: 280px !important;
            width: 100% !important;
        }}

        .main > .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 2.5rem;
        }}
        .card-box, .chart-card, .feature-card, .team-card {{ padding: 16px 18px; }}
        .cg-hero {{ padding: 6px 0 16px 0; }}

        [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
        [data-testid="column"] {{ min-width: 100% !important; }}
    }}
    </style>
""", unsafe_allow_html=True)


# ── Hero Header ─────────────────────────────────────────────────────────────
st.markdown("""
    <div class="cg-hero">
        <div class="cg-hero-pill">✦ NEXT-GEN GOVERNANCE PLATFORM</div>
        <div class="cg-hero-title">🛡️ CyberGuard <span class="accent">AI</span></div>
        <div class="cg-hero-sub">
            Real-time contextual cyberbullying detection, transparent decision governance,
            and automated multi-tier policy enforcement powered by signal models & FAISS RAG.
        </div>
    </div>
""", unsafe_allow_html=True)


# ── Navigation Options & State ──────────────────────────────────────────────
nav_options = ["Home", "Features", "Tech Stack", "Team", "About"]
nav_icons = ["house-fill", "lightning-charge-fill", "cpu-fill", "people-fill", "info-circle-fill"]

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Home"

current_idx = nav_options.index(st.session_state.current_tab) if st.session_state.current_tab in nav_options else 0


# ── Desktop Top Navigation Bar (Visible on Desktop) ─────────────────────────
st.markdown('<div id="desktop-navbar-marker"></div>', unsafe_allow_html=True)
desktop_selected = option_menu(
    menu_title=None,
    options=nav_options,
    icons=nav_icons,
    menu_icon="shield-fill",
    default_index=current_idx,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "8px 12px",
            "background-color": f"{nav_bg} !important",
            "border-radius": "16px",
            "border": f"1px solid {border_val}",
            "margin-bottom": "26px",
            "box-shadow": "0 4px 20px -4px rgba(0,0,0,0.15)" if is_dark else "0 4px 20px -4px rgba(15,23,42,0.06)",
        },
        "icon": {"color": primary_val, "font-size": "16px"},
        "nav-link": {
            "font-size": "0.88rem",
            "font-weight": "600",
            "color": f"{nav_link_color} !important",
            "border-radius": "10px",
            "--hover-color": nav_hover_bg,
        },
        "nav-link-selected": {
            "background": "#2563EB !important",
            "color": "white !important",
            "box-shadow": "0 6px 16px rgba(37,99,235,0.28)",
        },
    },
    key="desktop_nav_menu",
)


# ── Mobile Sidebar Navigation (Triggered by Top-Left ☰ Menu Button) ─────────
with st.sidebar:
    header_title_color = "#F8FAFC" if is_dark else "#0F172A"
    header_sub_color = "#94A3B8" if is_dark else "#64748B"
    st.markdown(f"""
        <div style="padding: 12px 0 20px 0; text-align: center; border-bottom: 1px solid {border_val}; margin-bottom: 16px;">
            <div style="font-size: 1.25rem; font-weight: 800; color: {header_title_color};">🛡️ CyberGuard AI</div>
            <div style="font-size: 0.8rem; color: {header_sub_color}; font-weight: 600; margin-top: 4px;">Navigation</div>
        </div>
    """, unsafe_allow_html=True)

    mobile_selected = option_menu(
        menu_title=None,
        options=nav_options,
        icons=nav_icons,
        default_index=current_idx,
        orientation="vertical",
        styles={
            "container": {
                "padding": "0px",
                "background-color": "transparent !important",
                "border": "none",
            },
            "icon": {"color": primary_val, "font-size": "16px"},
            "nav-link": {
                "font-size": "0.92rem",
                "font-weight": "600",
                "color": f"{nav_link_color} !important",
                "border-radius": "10px",
                "padding": "10px 14px",
                "margin-bottom": "6px",
                "--hover-color": nav_hover_bg,
            },
            "nav-link-selected": {
                "background": "#2563EB !important",
                "color": "white !important",
                "box-shadow": "0 4px 12px rgba(37,99,235,0.25)",
            },
        },
        key="mobile_sidebar_menu",
    )



# ── Synchronize Selected Navigation Tab ────────────────────────────────────
if desktop_selected and desktop_selected != st.session_state.current_tab:
    st.session_state.current_tab = desktop_selected
    st.rerun()
elif mobile_selected and mobile_selected != st.session_state.current_tab:
    st.session_state.current_tab = mobile_selected
    st.rerun()

selected_tab = st.session_state.current_tab



# ── Route to Tabs ─────────────────────────────────────────────────────────
if selected_tab == "Home":
    from src.ui.home import render_home_tab
    render_home_tab()

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

