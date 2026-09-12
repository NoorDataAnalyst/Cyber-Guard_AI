"""
Streamlit Web Application Entry Point (Thin Monolithic UI).
Provides two primary views:
1. Live Feed view (simulated chat interface with visual severity badges, manual user report buttons, and expandable reasoning drawers)
2. Admin Dashboard view (comprehensive audit table, RAG inspection drawers, and Admin manual override authority controls)
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from src.config import SEVERITY_LEVELS, CATEGORIES, LEGAL_DISCLAIMER
from src.pipeline import CyberbullyingPipeline
from src.db import (
    get_conversation_thread,
    get_flagged_verdicts,
    update_admin_status,
    save_message,
)
from src.policy import apply_admin_override

# Page Config
st.set_page_config(
    page_title="Cyberbullying Detection & RAG Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Vanilla CSS for Glassmorphism & High-Contrast Severity Badges)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stAppHeader {
        background: rgba(14, 17, 23, 0.8);
    }
    .badge-none {
        background-color: #2e7d32; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem;
    }
    .badge-mild {
        background-color: #f57f17; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem;
    }
    .badge-moderate {
        background-color: #e65100; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem;
    }
    .badge-severe {
        background-color: #c62828; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem;
    }
    .card-box {
        background: #1e222d; border-radius: 10px; padding: 18px; margin-bottom: 15px; border: 1px solid #2d3241;
    }
    .legal-box {
        background-color: #1a2332; border-left: 4px solid #0288d1; padding: 12px 15px; border-radius: 4px; font-size: 0.9rem; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline():
    """Cache pipeline instantiation to avoid reloading models on every rerender."""
    return CyberbullyingPipeline()


pipeline = get_pipeline()


def render_severity_badge(severity: str) -> str:
    sev = str(severity).lower()
    if sev == "severe":
        return '<span class="badge-severe">🔴 SEVERE</span>'
    elif sev == "moderate":
        return '<span class="badge-moderate">🟠 MODERATE</span>'
    elif sev == "mild":
        return '<span class="badge-mild">🟡 MILD</span>'
    else:
        return '<span class="badge-none">🟢 CLEAN</span>'


# Sidebar Navigation & Settings
st.sidebar.title("🛡️ CyberGuard AI")
st.sidebar.caption("Context & Emotion-Aware RAG Cyberbullying System")

view_mode = st.sidebar.radio(
    "Select Interface View",
    ["💬 Live Chat Feed", "📊 Admin Governance Dashboard"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Pipeline Configuration")
user_name = st.sidebar.text_input("Simulated User Name", value="User_Alpha")
st.sidebar.info("Pretrained Models: toxic-bert & roberta-go_emotions\nVector Index: FAISS CPU\nLaw Corpus: PECA 2016 & FIA Pakistan")

# ==============================================================================
# VIEW 1: LIVE CHAT FEED
# ==============================================================================
if view_mode == "💬 Live Chat Feed":
    st.title("💬 Live Chat Conversation Feed")
    st.caption("Simulate real-time online messages. System automatically scans every message, and users can manually report suspicious content.")

    # Display Chat Messages
    thread_messages = get_conversation_thread(limit=50)

    for msg in thread_messages:
        sender = msg.get("sender", "Anonymous")
        is_user = (sender == user_name)
        avatar = "👤" if is_user else "💬"
        
        with st.chat_message(sender, avatar=avatar):
            is_flagged = bool(msg.get("is_flagged", False))
            severity = msg.get("severity") or "none"
            action_taken = msg.get("action_taken") or "no action"

            col_msg, col_badge = st.columns([0.8, 0.2])
            with col_msg:
                st.markdown(f"**{sender}**: {msg['text']}")
            with col_badge:
                if is_flagged:
                    st.markdown(render_severity_badge(severity), unsafe_allow_html=True)

            # Manual User Report Action Button
            col_rep, col_exp = st.columns([0.2, 0.8])
            with col_rep:
                if not is_flagged:
                    if st.button("🚩 Report", key=f"rep_{msg['id']}"):
                        with st.spinner("Analyzing manual user report via RAG + LLM agent..."):
                            pipeline.process_message(
                                sender=sender,
                                text=msg['text'],
                                report_type="manual_user_report",
                                force_flag=True
                            )
                        st.success("Message reported to Admin review queue.")
                        st.rerun()

            # Expandable Reasoning & User Report Drawer for Flagged Items
            if is_flagged:
                with st.expander(f"🔍 Why was this flagged? (Action: {str(action_taken).title()})"):
                    st.markdown(f"**Category**: `{msg.get('category') or 'N/A'}`")
                    st.markdown(f"**Action Enforced**: `{action_taken}`")
                    
                    if msg.get("explanation"):
                        st.markdown(f"**Internal Admin Explanation**:\n_{msg['explanation']}_")

                    if msg.get("user_report"):
                        st.markdown("<div class='legal-box'>", unsafe_allow_html=True)
                        st.markdown(f"**User-Facing Policy Notice**:\n\n{msg['user_report']}")
                        st.markdown("</div>", unsafe_allow_html=True)

    # Chat Input Box
    new_message = st.chat_input("Type a message to post into the conversation...")
    if new_message:
        with st.spinner("Running Signal Layer (Toxicity & Emotion) and RAG Reasoning..."):
            result = pipeline.process_message(sender=user_name, text=new_message, report_type="automatic")
        st.rerun()

# ==============================================================================
# VIEW 2: ADMIN GOVERNANCE DASHBOARD
# ==============================================================================
else:
    st.title("📊 Admin Governance & Audit Dashboard")
    st.caption("Inspect all flagged cyberbullying items, inspect RAG context & precedent matches, and exercise Admin manual override authority.")

    # Filter Controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sev_filter = st.selectbox("Filter by Severity", ["all"] + SEVERITY_LEVELS)
    with col_f2:
        cat_filter = st.selectbox("Filter by Category", ["all"] + CATEGORIES)

    flagged_items = get_flagged_verdicts(severity_filter=sev_filter, category_filter=cat_filter)

    if not flagged_items:
        st.info("No flagged messages found matching selected filters.")
    else:
        st.write(f"Total Flagged Items: **{len(flagged_items)}**")

        for item in flagged_items:
            verdict_id = item["verdict_id"]
            severity = item.get("severity") or "none"
            category = item.get("category") or "N/A"
            action_taken = item.get("action_taken") or "no action"
            admin_status = item.get("admin_status") or "pending"

            with st.container():
                st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([0.15, 0.45, 0.20, 0.20])

                with c1:
                    st.markdown(render_severity_badge(severity), unsafe_allow_html=True)
                    st.caption(f"Status: `{admin_status}`")

                with c2:
                    st.markdown(f"**{item.get('sender', 'User')}**: {item['message_text']}")
                    st.caption(f"Timestamp: {item.get('timestamp', '')[:19]} | Mode: `{item.get('report_type', 'automatic')}`")

                with c3:
                    st.markdown(f"Category: **{category}**")
                    st.markdown(f"Toxicity Score: **{item.get('toxicity_score', 0.0):.2f}**")
                    st.markdown(f"Emotion: **{item.get('top_emotion', 'neutral')}**")

                with c4:
                    st.markdown(f"Action: **{action_taken}**")

                # Full Inspection Accordion
                with st.expander(f"🔎 Detailed Audit Drawer & RAG Inspection (ID #{verdict_id})"):
                    t1, t2, t3, t4 = st.tabs(["🤖 LLM Verdict", "📚 RAG Precedents", "📜 Law & Policy", "🛠️ Admin Override"])

                    with t1:
                        st.markdown(f"**Is True Positive**: `{item.get('is_true_positive')}`")
                        st.markdown(f"**LLM Confidence**: `{item.get('confidence', 0.0):.2f}`")
                        st.markdown(f"**Internal Admin Explanation**:\n\n_{item.get('explanation')}_")

                    with t2:
                        st.markdown("#### Retrieved Thread History Context")
                        st.json(item.get("context_retrieved", []))
                        
                        st.markdown("#### Retrieved Top Precedent Examples")
                        for idx, ex in enumerate(item.get("examples_retrieved", []), 1):
                            st.markdown(f"**{idx}. Example**: \"{ex.get('text')}\" | Category: `{ex.get('category')}` | Sim Score: `{ex.get('similarity_score', 0.0):.2f}`")

                    with t3:
                        st.markdown("#### Retrieved Policy & Legal Framework Snippets")
                        for idx, pol in enumerate(item.get("policy_retrieved", []), 1):
                            st.markdown(f"**Source**: {pol.get('source')}")
                            st.markdown(f"> \"{pol.get('snippet')}\"")
                        
                        if item.get("user_report"):
                            st.markdown("#### Generated User-Facing Report")
                            st.text_area("Report Content", value=item["user_report"], height=160, key=f"rep_txt_{verdict_id}")

                    with t4:
                        st.markdown("#### Admin Manual Override Authority Controls")
                        st.caption("As an authorized admin moderator, you can override system actions, manually block/unblock, or dismiss false positives.")

                        note_input = st.text_input("Admin Reason / Note", value=item.get("admin_note", ""), key=f"note_{verdict_id}")

                        b_col1, b_col2, b_col3 = st.columns(3)
                        with b_col1:
                            if st.button("🚫 Force Block User", key=f"btn_blk_{verdict_id}"):
                                updated = apply_admin_override(item, "block_message", admin_note=note_input)
                                update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_input)
                                st.success("User/Message manually blocked by Admin.")
                                st.rerun()

                        with b_col2:
                            if st.button("✅ Force Unblock User", key=f"btn_unblk_{verdict_id}"):
                                updated = apply_admin_override(item, "unblock_message", admin_note=note_input)
                                update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_input)
                                st.success("User/Message manually unblocked by Admin.")
                                st.rerun()

                        with b_col3:
                            if st.button("🗑️ Dismiss Flag (Clean)", key=f"btn_dsm_{verdict_id}"):
                                updated = apply_admin_override(item, "dismiss_flag", admin_note=note_input)
                                update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_input)
                                st.success("Flag dismissed as clean.")
                                st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
