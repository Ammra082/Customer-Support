"""Reusable Streamlit UI components for the TaskFlow Support Bot."""

import streamlit as st
from datetime import datetime


# ── Theme constants ───────────────────────────────────────────────────────────

PRIMARY = "#6366F1"        # Indigo
SURFACE = "#1E1E2E"        # Dark surface
SURFACE_2 = "#2A2A3E"      # Slightly lighter
SUCCESS = "#22C55E"        # Green
WARNING = "#F59E0B"        # Amber
DANGER = "#EF4444"         # Red
TEXT_MUTED = "#94A3B8"     # Slate-400


def intent_badge(intent: str) -> str:
    """Return a coloured HTML badge for the given intent."""
    colors = {
        "faq": "#3B82F6",       # blue
        "action": "#8B5CF6",    # violet
        "escalate": "#EF4444",  # red
        "unknown": "#6B7280",   # gray
    }
    color = colors.get(intent.lower(), "#6B7280")
    label = intent.upper()
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.72rem;font-weight:600;'
        f'letter-spacing:0.05em;">{label}</span>'
    )


def confidence_bar(score: float) -> str:
    """Return an HTML progress bar representing confidence."""
    pct = int(score * 100)
    if pct >= 75:
        color = SUCCESS
    elif pct >= 45:
        color = WARNING
    else:
        color = DANGER
    return (
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="flex:1;background:#374151;border-radius:4px;height:6px;">'
        f'<div style="width:{pct}%;background:{color};border-radius:4px;height:6px;'
        f'transition:width 0.4s ease;"></div></div>'
        f'<span style="font-size:0.75rem;color:{TEXT_MUTED};min-width:36px;">{pct}%</span>'
        f'</div>'
    )


def message_bubble(role: str, content: str, meta: dict | None = None) -> None:
    """Render a chat message bubble."""
    is_user = role == "user"
    align = "flex-end" if is_user else "flex-start"
    bg = "#4F46E5" if is_user else SURFACE_2
    text_color = "white" if is_user else "#E2E8F0"
    border_radius = "18px 18px 4px 18px" if is_user else "18px 18px 18px 4px"

    st.markdown(
        f'<div style="display:flex;justify-content:{align};margin-bottom:8px;">'
        f'<div style="max-width:78%;background:{bg};color:{text_color};'
        f'padding:10px 16px;border-radius:{border_radius};'
        f'font-size:0.92rem;line-height:1.55;word-wrap:break-word;">'
        f'{content}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def meta_panel(intent: str, confidence: float, escalated: bool, ticket_number: str | None) -> None:
    """Render the intent / confidence / escalation metadata strip."""
    cols = st.columns([1, 2, 1])
    with cols[0]:
        st.markdown("**Intent**")
        st.markdown(intent_badge(intent), unsafe_allow_html=True)
    with cols[1]:
        st.markdown("**Confidence**")
        st.markdown(confidence_bar(confidence), unsafe_allow_html=True)
    with cols[2]:
        if escalated:
            st.markdown("**Escalated**")
            ticket_label = ticket_number or "—"
            st.markdown(
                f'<span style="color:{DANGER};font-weight:700;">⚠ {ticket_label}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("**Status**")
            st.markdown(
                f'<span style="color:{SUCCESS};font-weight:700;">✓ Resolved</span>',
                unsafe_allow_html=True,
            )


def ticket_row_card(ticket: dict) -> None:
    """Render a single ticket as a compact card."""
    status_colors = {
        "open": DANGER,
        "in_progress": WARNING,
        "resolved": SUCCESS,
        "closed": TEXT_MUTED,
    }
    status = ticket.get("status", "open")
    color = status_colors.get(status, TEXT_MUTED)
    created = ticket.get("created_at", "")
    if hasattr(created, "strftime"):
        created_str = created.strftime("%Y-%m-%d %H:%M")
    else:
        created_str = str(created)[:16]

    st.markdown(
        f'<div style="background:{SURFACE_2};border-left:4px solid {color};'
        f'border-radius:8px;padding:12px 16px;margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-weight:700;color:#E2E8F0;font-size:0.9rem;">'
        f'{ticket.get("ticket_number","")}</span>'
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.72rem;font-weight:600;">'
        f'{status.upper()}</span></div>'
        f'<div style="color:{TEXT_MUTED};font-size:0.8rem;margin-top:4px;">'
        f'User: <b>{ticket.get("user_id","")}</b> &nbsp;|&nbsp; {created_str}'
        f'</div>'
        f'<div style="color:#CBD5E1;font-size:0.82rem;margin-top:6px;">'
        f'<b>Reason:</b> {ticket.get("escalation_reason","—")}</div>'
        f'<div style="color:{TEXT_MUTED};font-size:0.78rem;margin-top:4px;font-style:italic;">'
        f'"{ticket.get("conversation_snippet","")[:100]}..."</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def inject_global_css() -> None:
    """Inject global CSS overrides for a polished dark theme."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #0F0F1A !important;
            color: #E2E8F0 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #13131F !important;
            border-right: 1px solid #2A2A3E;
        }

        /* Main content */
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 900px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: #1E1E2E;
            border-radius: 10px;
            padding: 4px;
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #94A3B8 !important;
            border-radius: 8px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
        }
        .stTabs [aria-selected="true"] {
            background: #6366F1 !important;
            color: white !important;
        }

        /* Input */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: #1E1E2E !important;
            color: #E2E8F0 !important;
            border: 1px solid #2A2A3E !important;
            border-radius: 10px !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 2px rgba(99,102,241,0.25) !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 8px 20px !important;
            transition: opacity 0.2s !important;
        }
        .stButton > button:hover { opacity: 0.88 !important; }

        /* Metrics */
        [data-testid="metric-container"] {
            background: #1E1E2E;
            border: 1px solid #2A2A3E;
            border-radius: 10px;
            padding: 12px 16px;
        }

        /* Divider */
        hr { border-color: #2A2A3E !important; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0F0F1A; }
        ::-webkit-scrollbar-thumb { background: #2A2A3E; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
