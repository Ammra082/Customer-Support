"""TaskFlow Support Bot — Streamlit Frontend Application."""

import uuid
import requests
import streamlit as st
from datetime import datetime

from app.ui.components import (
    inject_global_css,
    message_bubble,
    meta_panel,
    ticket_row_card,
    PRIMARY, SUCCESS, DANGER, TEXT_MUTED, SURFACE_2,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TaskFlow Support",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_global_css()

# ── Config ─────────────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_USER = "demo_user"
REQUEST_TIMEOUT = 60


# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {role, content, meta}
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = DEFAULT_USER
if "last_meta" not in st.session_state:
    st.session_state.last_meta = None


# ── Helper functions ───────────────────────────────────────────────────────────

def send_message(message: str) -> dict | None:
    """POST to /chat and return the JSON response."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "user_id": st.session_state.user_id,
                "conversation_id": st.session_state.conversation_id,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"API error {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(
            "⚠️ Cannot connect to the backend. "
            "Make sure `uvicorn app.main:app` is running."
        )
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def fetch_tickets() -> list[dict]:
    """GET /tickets and return the list."""
    try:
        resp = requests.get(f"{BACKEND_URL}/tickets", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("tickets", [])
        return []
    except Exception:
        return []


def reset_conversation() -> None:
    """Reset session state and optionally clear backend data."""
    st.session_state.messages = []
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.last_meta = None


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center;padding:20px 0 10px;">
        <div style="display:inline-flex;align-items:center;gap:10px;">
            <span style="font-size:2rem;">⚡</span>
            <span style="font-size:1.75rem;font-weight:800;
                background:linear-gradient(135deg,#6366F1,#A78BFA);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                TaskFlow Support
            </span>
        </div>
        <p style="color:{TEXT_MUTED};margin-top:4px;font-size:0.9rem;">
            AI-powered customer support &nbsp;·&nbsp; Powered by Llama 3.3 70B
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_chat, tab_admin = st.tabs(["💬  Customer Chat", "🎫  Admin Tickets"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CUSTOMER CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    # ── Sidebar-style controls at the top ──────────────────────────────────
    with st.expander("⚙️  Session Settings", expanded=False):
        col_uid, col_cid = st.columns(2)
        with col_uid:
            new_uid = st.text_input("User ID", value=st.session_state.user_id, key="uid_input")
            if new_uid != st.session_state.user_id:
                st.session_state.user_id = new_uid
                reset_conversation()
                st.rerun()
        with col_cid:
            st.text_input(
                "Conversation ID",
                value=st.session_state.conversation_id,
                disabled=True,
                key="cid_display",
            )
        if st.button("🔄  New Conversation", key="new_convo_btn"):
            reset_conversation()
            st.rerun()

    # ── Last-turn metadata strip ────────────────────────────────────────────
    if st.session_state.last_meta:
        m = st.session_state.last_meta
        st.markdown("---")
        st.markdown(
            f'<div style="font-size:0.8rem;color:{TEXT_MUTED};'
            f'margin-bottom:4px;">Last response metadata</div>',
            unsafe_allow_html=True,
        )
        meta_panel(
            intent=m.get("intent", "unknown"),
            confidence=m.get("confidence", 0.0),
            escalated=m.get("escalated", False),
            ticket_number=m.get("ticket_number"),
        )
        st.markdown("---")

    # ── Chat history ────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                f"""
                <div style="text-align:center;padding:40px 20px;color:{TEXT_MUTED};">
                    <div style="font-size:2.5rem;margin-bottom:12px;">🤖</div>
                    <div style="font-size:1rem;font-weight:600;color:#CBD5E1;">
                        Hello! I'm your TaskFlow support assistant.
                    </div>
                    <div style="font-size:0.875rem;margin-top:8px;">
                        Ask me anything about your account, billing, or workspace.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.messages:
                message_bubble(msg["role"], msg["content"])

    # ── Input area ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([6, 1])
        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder="Type your message here...",
                label_visibility="collapsed",
                key="chat_input",
            )
        with col_send:
            submitted = st.form_submit_button("Send", use_container_width=True)

    # ── Quick prompts ───────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:{TEXT_MUTED};font-size:0.78rem;margin:4px 0 8px;">Quick prompts:</div>',
        unsafe_allow_html=True,
    )
    q_cols = st.columns(4)
    quick_prompts = [
        "Check my subscription",
        "How do I reset my password?",
        "Upgrade to Pro plan",
        "Talk to a human agent",
    ]
    quick_trigger = None
    for i, prompt in enumerate(quick_prompts):
        with q_cols[i]:
            if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                quick_trigger = prompt

    # ── Process message ─────────────────────────────────────────────────────
    final_input = None
    if submitted and user_input.strip():
        final_input = user_input.strip()
    elif quick_trigger:
        final_input = quick_trigger

    if final_input:
        # Add user message immediately
        st.session_state.messages.append({"role": "user", "content": final_input})

        with st.spinner("Thinking..."):
            response_data = send_message(final_input)

        if response_data:
            bot_response = response_data.get("response", "I'm sorry, something went wrong.")
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # Store metadata for the strip
            st.session_state.last_meta = {
                "intent": response_data.get("intent", "unknown"),
                "confidence": response_data.get("confidence", 0.0),
                "escalated": response_data.get("escalated", False),
                "ticket_number": response_data.get("ticket_number"),
                "action_result": response_data.get("action_result"),
            }

        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ADMIN TICKETS
# ══════════════════════════════════════════════════════════════════════════════
with tab_admin:
    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
            <h2 style="font-size:1.3rem;font-weight:700;margin:0;">
                🎫 Escalated Support Tickets
            </h2>
            <p style="color:{TEXT_MUTED};font-size:0.85rem;margin-top:4px;">
                All conversations escalated to human support agents.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_refresh, col_stats = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄  Refresh", key="refresh_tickets"):
            st.rerun()

    tickets = fetch_tickets()

    if not tickets:
        st.markdown(
            f"""
            <div style="text-align:center;padding:60px 20px;color:{TEXT_MUTED};">
                <div style="font-size:2rem;margin-bottom:10px;">✅</div>
                <div style="font-weight:600;color:#CBD5E1;">No escalated tickets</div>
                <div style="font-size:0.85rem;margin-top:6px;">
                    All conversations are being handled autonomously.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Summary metrics
        total = len(tickets)
        open_count = sum(1 for t in tickets if t.get("status") == "open")
        resolved_count = sum(1 for t in tickets if t.get("status") == "resolved")
        in_progress_count = sum(1 for t in tickets if t.get("status") == "in_progress")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("Open", open_count)
        m3.metric("In Progress", in_progress_count)
        m4.metric("Resolved", resolved_count)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Filter bar
        filter_col, sort_col = st.columns([2, 1])
        with filter_col:
            status_filter = st.selectbox(
                "Filter by status",
                options=["All", "open", "in_progress", "resolved", "closed"],
                key="status_filter",
            )
        with sort_col:
            sort_order = st.selectbox(
                "Sort",
                options=["Newest first", "Oldest first"],
                key="sort_order",
            )

        # Apply filters
        filtered = tickets if status_filter == "All" else [
            t for t in tickets if t.get("status") == status_filter
        ]
        if sort_order == "Oldest first":
            filtered = list(reversed(filtered))

        st.markdown(
            f'<div style="color:{TEXT_MUTED};font-size:0.82rem;margin-bottom:12px;">'
            f'Showing {len(filtered)} of {total} tickets</div>',
            unsafe_allow_html=True,
        )

        # Render ticket cards
        for ticket in filtered:
            ticket_row_card(ticket)

        # Table view toggle
        with st.expander("📊  Table View", expanded=False):
            import pandas as pd
            df = pd.DataFrame(filtered)
            display_cols = [
                "ticket_number", "user_id", "status", "intent",
                "priority", "escalation_reason", "created_at",
            ]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(
                df[display_cols].rename(columns={
                    "ticket_number": "Ticket",
                    "user_id": "User",
                    "status": "Status",
                    "intent": "Intent",
                    "priority": "Priority",
                    "escalation_reason": "Reason",
                    "created_at": "Created",
                }),
                use_container_width=True,
                height=300,
            )
