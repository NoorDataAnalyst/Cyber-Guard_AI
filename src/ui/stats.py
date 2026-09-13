"""
Stats Tab Module: Plotly analytics dashboard for system-wide cyberbullying metrics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.db import get_analytics_data


SEVERITY_COLOR_MAP = {
    "severe":   "#DC2626",
    "moderate": "#D97706",
    "mild":     "#EAB308",
    "none":     "#16A34A",
    "clean":    "#16A34A",
}

CATEGORY_COLORS = [
    "#3B5BDB", "#EC4899", "#F59E0B", "#16A34A",
    "#0EA5A5", "#8B5CF6", "#EF4444", "#6366F1",
]


def _make_metric_card(label: str, value, delta_label: str = "", color: str = "#3B5BDB") -> str:
    return f"""
    <div style="
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: var(--shadow-sm);
    ">
        <div style="font-size: 2.2rem; font-weight: 800; color: {color};">{value}</div>
        <div style="font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; font-weight: 600;">{label}</div>
        {f'<div style="font-size:0.78rem; color:var(--text-faint); margin-top:4px;">{delta_label}</div>' if delta_label else ''}
    </div>
    """


def render_stats_tab():
    is_dark = (st.session_state.get("theme") == "dark")
    text_col = "#F8FAFC" if is_dark else "#0F172A"
    sub_col  = "#94A3B8" if is_dark else "#475569"
    grid_col = "#263346" if is_dark else "#E5E7EB"

    # Shared styles (.chart-card, .stats-header) live globally in app.py.
    st.markdown("""
        <div class="stats-header">
            <h2>📈 Platform Analytics</h2>
            <p>Real-time aggregated metrics from the CyberGuard AI detection pipeline.</p>
        </div>
    """, unsafe_allow_html=True)

    # Load analytics data
    data = get_analytics_data()

    total_msgs = data.get("total_messages", 0)
    flagged_msgs = data.get("flagged_messages", 0)
    total_appeals = data.get("total_appeals", 0)
    pending_appeals = data.get("pending_appeals", 0)
    severity_counts = data.get("severity_counts", {})
    category_counts = data.get("category_counts", {})

    clean_msgs = total_msgs - flagged_msgs
    detection_rate = f"{(flagged_msgs / total_msgs * 100):.1f}%" if total_msgs > 0 else "—"

    # ── Metric cards row ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_make_metric_card("Total Messages", total_msgs, "all-time", "#3B82F6"), unsafe_allow_html=True)
    with c2:
        st.markdown(_make_metric_card("Flagged Messages", flagged_msgs, f"Detection rate: {detection_rate}", "#DC2626"), unsafe_allow_html=True)
    with c3:
        st.markdown(_make_metric_card("Total Appeals", total_appeals, f"{pending_appeals} pending", "#D97706"), unsafe_allow_html=True)
    with c4:
        st.markdown(_make_metric_card("Clean Messages", clean_msgs, "passed all checks", "#16A34A"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if total_msgs == 0:
        st.info("📭 No data yet. Send some messages in the Live Chat Feed to see analytics here.")
        return

    # ── Row 1: Severity Donut + Category Bar ─────────────────────────────────
    chart_col1, chart_col2 = st.columns([0.45, 0.55])

    with chart_col1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Severity Distribution")

        sev_labels = list(severity_counts.keys())
        sev_values = list(severity_counts.values())
        sev_colors = [SEVERITY_COLOR_MAP.get(s.lower(), "#888") for s in sev_labels]

        if sev_labels:
            fig_donut = go.Figure(go.Pie(
                labels=[s.upper() for s in sev_labels],
                values=sev_values,
                hole=0.55,
                marker=dict(colors=sev_colors, line=dict(color="#151D2A" if is_dark else "#FFFFFF", width=2)),
                textinfo="percent+label",
                textfont=dict(size=13, color="white"),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=text_col, size=13),
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(color=sub_col),
                    orientation="h",
                    y=-0.15,
                ),
                height=310,
                annotations=[dict(
                    text=f"<b>{flagged_msgs}</b><br><span style='font-size:11px'>Flagged</span>",
                    x=0.5, y=0.5,
                    font=dict(size=16, color=text_col),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, width="stretch")
        else:
            st.caption("No severity data available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("#### 📂 Category Breakdown")

        cat_items = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        cat_labels = [k.replace("_", " ").title() for k, _ in cat_items]
        cat_values = [v for _, v in cat_items]
        cat_colors_used = CATEGORY_COLORS[:len(cat_labels)]

        if cat_labels:
            fig_bar = go.Figure(go.Bar(
                x=cat_values,
                y=cat_labels,
                orientation="h",
                marker=dict(
                    color=cat_colors_used,
                    line=dict(color="rgba(0,0,0,0)"),
                ),
                text=[f"  {v}" for v in cat_values],
                textposition="outside",
                textfont=dict(color=text_col, size=12),
                hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=text_col, size=12),
                margin=dict(t=10, b=10, l=10, r=50),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=grid_col,
                    color=sub_col,
                    zeroline=False,
                ),
                yaxis=dict(
                    color=sub_col,
                    automargin=True,
                ),
                height=310,
                bargap=0.35,
            )
            st.plotly_chart(fig_bar, width="stretch")
        else:
            st.caption("No category data available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Row 2: Message Volume Gauge + Appeals Status ──────────────────────────
    gauge_col1, gauge_col2 = st.columns([0.5, 0.5])

    with gauge_col1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚡ Detection Rate Gauge")

        rate_val = (flagged_msgs / total_msgs * 100) if total_msgs > 0 else 0

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(rate_val, 1),
            number=dict(suffix="%", font=dict(color=text_col, size=36)),
            delta=dict(reference=20, suffix="%", increasing=dict(color="#DC2626"), decreasing=dict(color="#16A34A")),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=sub_col, tickfont=dict(color=sub_col)),
                bar=dict(color="#3B82F6"),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    dict(range=[0, 10], color="rgba(22,163,74,0.18)"),
                    dict(range=[10, 30], color="rgba(217,119,6,0.18)"),
                    dict(range=[30, 100], color="rgba(220,38,38,0.18)"),
                ],
                threshold=dict(
                    line=dict(color="#DC2626", width=3),
                    thickness=0.75,
                    value=30,
                ),
            ),
            title=dict(text="Flagged / Total Messages", font=dict(color=sub_col, size=13)),
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=text_col),
            margin=dict(t=30, b=20, l=30, r=30),
            height=280,
        )
        st.plotly_chart(fig_gauge, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with gauge_col2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("#### 📬 Appeals Status")

        approved_appeals = total_appeals - pending_appeals - data.get("pending_appeals", 0)
        # Derive from db directly: pending vs resolved
        resolved = total_appeals - pending_appeals
        labels_ap = ["Pending", "Resolved"]
        values_ap = [pending_appeals, resolved]
        colors_ap = ["#D97706", "#16A34A"]

        if total_appeals > 0:
            fig_ap = go.Figure(go.Pie(
                labels=labels_ap,
                values=values_ap,
                hole=0.5,
                marker=dict(colors=colors_ap, line=dict(color="#151D2A" if is_dark else "#FFFFFF", width=2)),
                textinfo="percent+value",
                textfont=dict(size=13, color="white"),
                hovertemplate="<b>%{label}</b><br>%{value} appeals<extra></extra>",
            ))
            fig_ap.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=text_col),
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=sub_col)),
                height=280,
                annotations=[dict(
                    text=f"<b>{total_appeals}</b><br><span style='font-size:10px'>Total</span>",
                    x=0.5, y=0.5,
                    font=dict(size=16, color=text_col),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_ap, width="stretch")
        else:
            st.info("No appeals submitted yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    if severity_counts or category_counts:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Raw Metrics Table")
        rows = []
        for sev, cnt in severity_counts.items():
            rows.append({"Dimension": "Severity", "Label": sev.title(), "Count": cnt})
        for cat, cnt in category_counts.items():
            rows.append({"Dimension": "Category", "Label": cat.replace("_", " ").title(), "Count": cnt})
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
