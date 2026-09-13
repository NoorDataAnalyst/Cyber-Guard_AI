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
    authenticate_or_register_user,
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


@st.fragment(run_every="2s")
def render_realtime_chat_messages(current_username: str, current_email: str, is_restricted: bool):
    """
    Renders thread messages in a real-time auto-updating fragment.
    Automatically polls database every 2 seconds without triggering full page reloads.
    """
    thread_messages = get_conversation_thread(limit=50)

    for idx, msg in enumerate(thread_messages):
        sender = msg.get("sender", "Anonymous")
        is_user = (sender == current_username)
        avatar = "👤" if is_user else "💬"

        with st.chat_message(sender, avatar=avatar):
            is_flagged = bool(msg.get("is_flagged", False))
            severity = msg.get("severity") or "none"
            action_taken = msg.get("action_taken") or "no action"
            is_reported_or_scanned = bool(msg.get("is_reported") or msg.get("has_verdict"))

            col_msg, col_badge = st.columns([0.8, 0.2])
            with col_msg:
                st.markdown(f"**{sender}**: {msg['text']}")
            with col_badge:
                if is_flagged:
                    st.markdown(render_severity_badge(severity), unsafe_allow_html=True)
                elif is_reported_or_scanned:
                    st.markdown(render_severity_badge("none"), unsafe_allow_html=True)

            col_rep, col_exp = st.columns([0.2, 0.8])
            with col_rep:
                if not is_flagged and not is_restricted and not is_reported_or_scanned:
                    if st.button("🚩 Report", key=f"rep_{msg['id']}_{idx}"):
                        with st.spinner("Analyzing manual report..."):
                            res = pipeline.process_existing_message(
                                message_id=msg['id'],
                                report_type="manual_user_report"
                            )
                        if res.get("is_flagged"):
                            st.success("Reported to Admin queue.")
                        else:
                            st.info("Report analyzed: Content verified clean.")
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


def render_home_tab():
    # Shared styles (badges, cards, banners) are defined once, globally, in app.py.

    # ── 1. State Persistence Sync from URL Query Parameters ─────────────────
    if "username" not in st.session_state or not st.session_state["username"]:
        param_username = st.query_params.get("user", "")
        param_email = st.query_params.get("email", "")
        param_role = st.query_params.get("role", "")

        if param_username or param_email:
            user_info = get_or_create_user(param_username or "User", email=param_email)
            is_admin = (user_info.get("role") == "admin" or param_role == "admin")
            st.session_state["username"] = user_info["username"]
            st.session_state["user_id"] = user_info["user_id"]
            st.session_state["email"] = user_info.get("email", "")
            st.session_state["role"] = "admin" if is_admin else user_info.get("role", "user")
            st.session_state["is_admin"] = is_admin

    # ── 2. FIRST GATE: Sign-In Screen (Shown when not authenticated) ──────
    if "username" not in st.session_state or not st.session_state["username"]:
        st.markdown("""
            <div style="max-width: 440px; margin: 30px auto; background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 36px 32px; box-shadow: var(--shadow-md); text-align: center;">
                <div style="width: 56px; height: 56px; background: var(--primary-soft); border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.8rem; color: var(--primary); margin-bottom: 16px; border: 1px solid var(--border);">🔑</div>
                <h2 style="font-weight: 800; font-size: 1.45rem; color: var(--text); margin: 0 0 8px 0; letter-spacing: -0.02em;">Sign In to CyberGuard</h2>
                <p style="color: var(--text-muted); font-size: 0.92rem; margin: 0 0 22px 0; line-height: 1.6;">
                    Enter your account credentials below to sign in and continue.
                </p>
        """, unsafe_allow_html=True)

        col_f1, col_f2, col_f3 = st.columns([0.05, 0.9, 0.05])
        with col_f2:
            with st.form("onboarding_join_form", border=False):
                input_name = st.text_input("Full Name or Username", placeholder="e.g. Zeeshan Ahmad", key="start_name_key")
                input_email = st.text_input("Email Address", placeholder="e.g. user@example.com", key="start_email_key")
                input_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="start_pass_key")
                submit_btn = st.form_submit_button("🚀 Sign In / Continue", width="stretch")

                if submit_btn:
                    clean_name = input_name.strip()
                    clean_email = input_email.strip().lower()
                    clean_pass = input_pass.strip()

                    if not clean_email or "@" not in clean_email:
                        st.error("Please enter a valid email address.")
                    elif not clean_pass:
                        st.error("Please enter your password.")
                    else:
                        res = authenticate_or_register_user(username=clean_name, email=clean_email, password=clean_pass)
                        if not res.get("authenticated"):
                            st.error(res.get("error", "Authentication failed."))
                        else:
                            is_admin = (res.get("role") == "admin")
                            st.session_state["username"] = res["username"]
                            st.session_state["user_id"] = res["user_id"]
                            st.session_state["email"] = res.get("email", "")
                            st.session_state["role"] = res.get("role", "user")
                            st.session_state["is_admin"] = is_admin

                            # Store state in query params for reload persistence
                            st.query_params["user"] = res["username"]
                            if res.get("email"):
                                st.query_params["email"] = res["email"]
                            st.query_params["role"] = res.get("role", "user")

                            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ── 3. AUTHENTICATED USER DETAILS ───────────────────────────────────────
    current_username = st.session_state["username"]
    current_email = st.session_state.get("email", "")
    is_admin_session = st.session_state.get("is_admin", False) or st.session_state.get("role") == "admin"

    user_info = get_or_create_user(current_username, email=current_email)
    user_id = user_info["user_id"]
    st.session_state["user_id"] = user_id

    # Active user banner with Sign Out
    col_u1, col_u2 = st.columns([0.82, 0.18])
    with col_u1:
        email_display = f" ({user_info['email']})" if user_info.get('email') else ""
        role_label = "👑 ADMIN" if is_admin_session else "👤 USER"
        st.caption(f"Logged In: **{user_info['username']}**{email_display} | Role: `{role_label}`")
    with col_u2:
        if st.button("🚪 Sign Out", key="sign_out_btn"):
            st.session_state["username"] = None
            st.session_state["user_id"] = None
            st.session_state["email"] = None
            st.session_state["is_admin"] = False
            st.session_state["role"] = None
            st.query_params.clear()
            st.rerun()

    # ── 4. ROLE-BASED SCREEN RENDERING ────────────────────────────────────────

    # --------------------------------------------------------------------------
    # A) ADMINISTRATOR SCREEN (admin@cyberguard.ai / role='admin')
    # --------------------------------------------------------------------------
    if is_admin_session:
        st.subheader("🛡️ Administrator Governance Dashboard")
        st.caption("Review user appeals, audit flagged toxic messages, monitor live chat, and inspect system metrics.")

        admin_view_choice = st.radio(
            "Admin Control Section",
            ["🚨 Pending Appeals Review", "📋 Flagged Message Audits", "💬 Live Chat Monitor"],
            horizontal=True
        )

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

        elif admin_view_choice == "📋 Flagged Message Audits":
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

        elif admin_view_choice == "💬 Live Chat Monitor":
            st.markdown("### Live Chat Stream Monitor")
            render_realtime_chat_messages(current_username, current_email, is_restricted=False)

        # Bottom System Analytics Section for Admin
        st.markdown("<br><hr style='border-top: 1px solid var(--border); margin: 36px 0 24px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📊 System Analytics & Governance Metrics")
        st.caption("Comprehensive system-wide analytics, toxicity distributions, and governance performance charts.")
        from src.ui.stats import render_stats_tab
        render_stats_tab()

    # --------------------------------------------------------------------------
    # B) REGULAR USER SCREEN (role='user')
    # --------------------------------------------------------------------------
    else:
        user_status_info = get_user_status(user_id)
        current_status = user_status_info["status"]
        is_restricted = current_status in ["muted", "blocked"]

        if current_status == "muted":
            mute_time_str = user_status_info.get("mute_expires_at", "30 minutes")
            if mute_time_str and len(mute_time_str) >= 19:
                mute_time_str = mute_time_str[:19].replace("T", " ") + " UTC"
            st.markdown(
                f"<div class='mute-banner'>"
                f"<h4>🔇 Account Muted</h4>"
                f"<p>Sending is temporarily restricted due to toxicity enforcement. Muted until: <code>{mute_time_str}</code>.</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        elif current_status == "blocked":
            st.markdown(
                f"<div class='restriction-banner'>"
                f"<h4>🚫 Account Suspended / Blocked</h4>"
                f"<p><b>Reason:</b> {user_status_info.get('reason', 'Violation of community standards')}</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        if is_restricted:
            pending_appeals = get_pending_appeals()
            user_pending = [a for a in pending_appeals if a["user_id"] == user_id]

            if user_pending:
                st.info("📩 **Admin Review Request Dispatched**: A review request has been sent to the Admin queue for review.")
                with st.expander("📝 Provide additional statement for the Admin"):
                    appeal_input = st.text_area("Explain why your restriction should be lifted:", height=100, key="appeal_update_area")
                    if st.button("Send Additional Statement to Admin", key="update_appeal_btn"):
                        if appeal_input.strip():
                            create_appeal(user_id=user_id, appeal_text=appeal_input.strip())
                            st.success("Your statement has been sent to the Admin queue!")
                            st.rerun()
                        else:
                            st.warning("Please enter an explanation before submitting.")
            else:
                st.markdown("### 📝 Send Appeal / Review Request to Admin")
                appeal_input = st.text_area("Explain why your restriction should be lifted:", height=100, key="appeal_text_area")
                if st.button("Submit Request to Admin Queue", key="submit_appeal_btn"):
                    if appeal_input.strip():
                        create_appeal(user_id=user_id, appeal_text=appeal_input.strip())
                        st.success("Your appeal request has been submitted successfully!")
                        st.rerun()
                    else:
                        st.warning("Please enter an explanation before submitting.")

        # Render Real-Time Chat Feed directly
        render_realtime_chat_messages(current_username, current_email, is_restricted)

        # Chat Input
        if is_restricted:
            st.chat_input("Messaging is disabled while your account is restricted.", disabled=True)
        else:
            new_message = st.chat_input("Type a message to post into the conversation...")
            if new_message:
                with st.spinner("Processing message..."):
                    res = pipeline.process_message(
                        sender=current_username,
                        text=new_message,
                        report_type="automatic",
                        email=current_email
                    )
                    if res.get("status") == "restricted":
                        st.error(f"Message rejected: Account is currently {res.get('user_status')}.")
                st.rerun()
