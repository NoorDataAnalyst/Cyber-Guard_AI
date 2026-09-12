"""
Home Tab Module: Live Chat Feed & Admin Governance Dashboard.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from src.config import SEVERITY_LEVELS, CATEGORIES, LEGAL_DISCLAIMER
from src.pipeline import CyberbullyingPipeline
from src.db import (
    get_or_create_user,
    get_user_status,
    get_conversation_thread,
    get_flagged_verdicts,
    update_admin_status,
    create_appeal,
    get_pending_appeals,
    resolve_appeal,
)
from src.policy import apply_admin_override


@st.cache_resource
def get_pipeline():
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


def render_home_tab():
    st.markdown("""
        <style>
        .badge-none { background-color: #2e7d32; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
        .badge-mild { background-color: #f57f17; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
        .badge-moderate { background-color: #e65100; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
        .badge-severe { background-color: #c62828; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
        .card-box { background: #1e222d; border-radius: 10px; padding: 18px; margin-bottom: 15px; border: 1px solid #2d3241; }
        .legal-box { background-color: #1a2332; border-left: 4px solid #0288d1; padding: 12px 15px; border-radius: 4px; font-size: 0.9rem; margin-top: 10px; }
        .restriction-banner { background-color: #3e1212; border: 1px solid #b71c1c; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #ffcdd2; }
        .mute-banner { background-color: #332606; border: 1px solid #f57f17; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #ffe0b2; }
        </style>
    """, unsafe_allow_html=True)

    # Sub-tab navigation within Home tab
    sub_tab1, sub_tab2 = st.tabs(["💬 Live Chat Feed", "📊 Admin Governance Dashboard"])

    # ==========================================================================
    # SUB-TAB 1: LIVE CHAT FEED
    # ==========================================================================
    with sub_tab1:
        st.subheader("💬 Live Chat Feed & Real-Time Monitoring")

        # Username Identity Session Handler (Correction #1 & #3)
        if "username" not in st.session_state or not st.session_state["username"]:
            st.info("👋 Welcome! Please enter your username to join the conversation.")
            input_name = st.text_input("Username", value="User_Alpha", key="user_input_key")
            if st.button("Join Conversation", key="join_btn"):
                user_info = get_or_create_user(input_name)
                st.session_state["username"] = user_info["username"]
                st.session_state["user_id"] = user_info["user_id"]
                st.rerun()
            return

        current_username = st.session_state["username"]
        user_info = get_or_create_user(current_username)
        user_id = user_info["user_id"]
        st.session_state["user_id"] = user_id

        # Fresh non-cached read of User Status (Correction #4)
        user_status_info = get_user_status(user_id)
        current_status = user_status_info["status"]

        # Display active user identity banner
        col_u1, col_u2 = st.columns([0.8, 0.2])
        with col_u1:
            st.caption(f"Active Identity: **{user_info['username']}** (ID: {user_id}) | Account Status: `{current_status.upper()}`")
        with col_u2:
            if st.button("Switch Identity", key="switch_id_btn"):
                st.session_state["username"] = None
                st.rerun()

        # Handle Restricted States (Muted / Blocked)
        is_restricted = current_status in ["muted", "blocked"]

        if current_status == "muted":
            mute_time_str = user_status_info.get("mute_expires_at", "30 minutes")
            if mute_time_str and len(mute_time_str) >= 19:
                mute_time_str = mute_time_str[:19].replace("T", " ") + " UTC"
            st.markdown(
                f"<div class='mute-banner'>"
                f"<h4>🔇 Account Muted</h4>"
                f"<p>Sending is temporarily restricted due to moderate toxicity enforcement. "
                f"<b>Mute Static Timestamp:</b> You are muted until <code>{mute_time_str}</code> (auto-clears on expiration).</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        elif current_status == "blocked":
            st.markdown(
                f"<div class='restriction-banner'>"
                f"<h4>🚫 Account Suspended / Blocked</h4>"
                f"<p><b>Reason:</b> {user_status_info.get('reason', 'Severe violation of community standards')}</p>"
                f"<p>Your sending privileges have been restricted. You may submit an appeal below for Admin review.</p>"
                f"</div>",
                unsafe_allow_html=True
            )

            # Check if user already submitted an appeal
            pending_appeals = get_pending_appeals()
            user_pending = [a for a in pending_appeals if a["user_id"] == user_id]

            if user_pending:
                st.info("⏳ **Your appeal is currently under review by an administrator.** Please check back later.")
            else:
                st.markdown("### 📝 Submit Account Ban Appeal")
                appeal_input = st.text_area("Explain why your account restriction should be lifted:", height=100, key="appeal_text_area")
                if st.button("Submit Appeal to Admin Queue", key="submit_appeal_btn"):
                    if appeal_input.strip():
                        create_appeal(user_id=user_id, appeal_text=appeal_input.strip())
                        st.success("Your appeal has been submitted successfully! Admins have been notified.")
                        st.rerun()
                    else:
                        st.warning("Please enter an explanation before submitting.")

        # Render Conversation History
        thread_messages = get_conversation_thread(limit=50)

        for msg in thread_messages:
            sender = msg.get("sender", "Anonymous")
            is_user = (sender == current_username)
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

                col_rep, col_exp = st.columns([0.2, 0.8])
                with col_rep:
                    if not is_flagged and not is_restricted:
                        if st.button("🚩 Report", key=f"rep_{msg['id']}"):
                            with st.spinner("Analyzing manual report..."):
                                pipeline.process_message(
                                    sender=current_username,
                                    text=msg['text'],
                                    report_type="manual_user_report",
                                    force_flag=True
                                )
                            st.success("Reported to Admin queue.")
                            st.rerun()

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

        # Chat Input (Disabled if user is blocked or muted)
        if is_restricted:
            st.chat_input("Messaging is disabled while your account is restricted.", disabled=True)
        else:
            new_message = st.chat_input("Type a message to post into the conversation...")
            if new_message:
                with st.spinner("Running Signal Layer (Toxicity & Emotion) and RAG Reasoning..."):
                    res = pipeline.process_message(sender=current_username, text=new_message, report_type="automatic")
                    if res.get("status") == "restricted":
                        st.error(f"Message rejected: Account is currently {res.get('user_status')}.")
                st.rerun()

    # ==========================================================================
    # SUB-TAB 2: ADMIN GOVERNANCE DASHBOARD
    # ==========================================================================
    with sub_tab2:
        st.subheader("📊 Admin Governance & Appeals Review")

        # Admin Password Gate with Session Persistence (Correction #6)
        expected_password = ""
        try:
            if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets:
                expected_password = st.secrets["ADMIN_PASSWORD"]
        except Exception:
            pass

        if not expected_password:
            expected_password = os.getenv("ADMIN_PASSWORD", "admin123")

        if not st.session_state.get("is_admin", False):
            st.warning("🔒 This section is password protected for authorized moderators.")
            pass_input = st.text_input("Enter Admin Password", type="password", key="admin_pass_input")
            if st.button("Unlock Admin Dashboard", key="unlock_admin_btn"):
                if pass_input == expected_password:
                    st.session_state["is_admin"] = True
                    st.success("Admin access granted!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            return

        st.success("🔑 Admin Session Active")

        admin_view_choice = st.radio("Admin Section", ["🚨 Pending Appeals Review", "📋 Flagged Message Audits"], horizontal=True)

        if admin_view_choice == "🚨 Pending Appeals Review":
            st.markdown("### Pending User Account Appeals")
            pending_list = get_pending_appeals()

            if not pending_list:
                st.info("No pending appeals at this time.")
            else:
                for app in pending_list:
                    with st.container():
                        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                        st.markdown(f"**User**: `{app['username']}` (ID: {app['user_id']}) | Submitted: `{app['submitted_at'][:19]}`")
                        st.markdown(f"**Blocked Reason**: {app['blocked_reason']} | Severity: `{app['severity']}`")
                        st.markdown(f"**User Appeal Statement**:\n> \"{app['appeal_text']}\"")

                        admin_note_inp = st.text_input("Admin Decision Note", key=f"note_app_{app['appeal_id']}")
                        c_app1, c_app2 = st.columns(2)

                        with c_app1:
                            if st.button("✅ Approve Appeal (Unblock User)", key=f"btn_app_{app['appeal_id']}"):
                                resolve_appeal(app['appeal_id'], decision="approved", admin_note=admin_note_inp)
                                st.success(f"Appeal approved for user '{app['username']}'. Account unblocked.")
                                st.rerun()

                        with c_app2:
                            if st.button("❌ Reject Appeal", key=f"btn_rej_{app['appeal_id']}"):
                                resolve_appeal(app['appeal_id'], decision="rejected", admin_note=admin_note_inp)
                                st.error(f"Appeal rejected for user '{app['username']}'. Account remains restricted.")
                                st.rerun()

                        st.markdown("</div>", unsafe_allow_html=True)

        else:
            # Audit List
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sev_filter = st.selectbox("Filter Severity", ["all"] + SEVERITY_LEVELS)
            with col_f2:
                cat_filter = st.selectbox("Filter Category", ["all"] + CATEGORIES)

            flagged_items = get_flagged_verdicts(severity_filter=sev_filter, category_filter=cat_filter)

            if not flagged_items:
                st.info("No flagged messages matching filters.")
            else:
                for item in flagged_items:
                    verdict_id = item["verdict_id"]
                    severity = item.get("severity") or "none"
                    category = item.get("category") or "N/A"
                    action_taken = item.get("action_taken") or "no action"
                    admin_status = item.get("admin_status") or "pending"

                    with st.container():
                        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
                        st.markdown(f"**{item.get('sender', 'User')}**: {item['message_text']}")
                        st.caption(f"Category: {category} | Severity: {severity} | Status: `{admin_status}` | Action: `{action_taken}`")

                        with st.expander(f"🔎 Audit Drawer (ID #{verdict_id})"):
                            st.markdown(f"**Explanation**: {item.get('explanation')}")
                            note_inp = st.text_input("Admin Reason / Note", value=item.get("admin_note", ""), key=f"note_audit_{verdict_id}")

                            ca1, ca2, ca3 = st.columns(3)
                            with ca1:
                                if st.button("🚫 Block User", key=f"btn_aud_blk_{verdict_id}"):
                                    updated = apply_admin_override(item, "block_message", admin_note=note_inp)
                                    update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_inp)
                                    st.success("User manually blocked.")
                                    st.rerun()
                            with ca2:
                                if st.button("✅ Unblock User", key=f"btn_aud_unblk_{verdict_id}"):
                                    updated = apply_admin_override(item, "unblock_message", admin_note=note_inp)
                                    update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_inp)
                                    st.success("User manually unblocked.")
                                    st.rerun()
                            with ca3:
                                if st.button("🗑️ Dismiss Flag", key=f"btn_aud_dsm_{verdict_id}"):
                                    updated = apply_admin_override(item, "dismiss_flag", admin_note=note_inp)
                                    update_admin_status(verdict_id, updated["admin_status"], updated["action_taken"], note_inp)
                                    st.success("Flag dismissed.")
                                    st.rerun()

                        st.markdown("</div>", unsafe_allow_html=True)
