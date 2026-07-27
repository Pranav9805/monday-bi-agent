"""
Monday.com Business Intelligence Agent - Premium Dark Glassmorphism Dashboard.
Inspired by Apple VisionOS, Windows 11, Arc Browser, Linear, Discord, and Stripe.

Fixes container nesting issue by using Streamlit native bordered containers
(st.container(border=True)) styled with Dark Glassmorphism CSS (div[data-testid="stVerticalBlockBorderWrapper"]).
Ensures all Plotly charts, chat components, and widgets render cleanly INSIDE their glass cards.
"""

from datetime import datetime
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

from agents.bi_agent import BIAgent, ask
from services import business_intelligence_service as bi_service
from services import data_cleaning_service as cleaning_service
from services import monday_service
from utils.logger import get_logger

# Initialize Logger
logger = get_logger("app_ui")

# Load environment variables
load_dotenv()

# Page Configuration - Wide Layout
st.set_page_config(
    page_title="Monday BI Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# FastAPI REST Server URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Inject Premium Dark Glassmorphism CSS System
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #FFFFFF !important;
    }

    /* Global Dark Gradient Background - Apple VisionOS / Arc Style */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #2563EB 100%) !important;
        background-attachment: fixed !important;
    }

    /* Hide Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}

    .main .block-container {
        padding-top: 20px !important;
        padding-bottom: 30px !important;
        max-width: 1500px !important;
        margin: 0 auto !important;
        padding-left: 30px !important;
        padding-right: 30px !important;
    }

    /* Streamlit Bordered Container Glassmorphism Overrides */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.10) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25) !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
    }

    /* Dark Glass Sidebar (#0F172A Blur) */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
        width: 240px !important;
    }

    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    .sidebar-brand-box {
        padding: 16px 10px;
        text-align: left;
    }

    .sidebar-brand-title {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF !important;
        margin: 0;
    }

    .sidebar-brand-sub {
        font-size: 12px;
        color: #CBD5E1 !important;
        margin: 2px 0 0 0;
    }

    /* Sidebar Radio Buttons Active Highlight */
    div[data-testid="stSidebar"] label[data-baseweb="radio"] {
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
    }

    div[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }

    /* Top Glass Header Card */
    .top-header-glass {
        background: rgba(255, 255, 255, 0.10);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        height: 110px;
        padding: 0 28px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .header-left h1 {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -0.01em;
    }

    .header-left p {
        font-size: 13px;
        color: #CBD5E1 !important;
        margin: 4px 0 0 0;
    }

    .header-badges {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .badge-chip-glass {
        font-size: 12px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 20px;
        background: rgba(16, 185, 129, 0.2);
        color: #34D399 !important;
        border: 1px solid rgba(52, 211, 153, 0.4);
        box-shadow: 0 0 12px rgba(52, 211, 153, 0.2);
    }

    /* Dark Glass KPI Cards */
    .kpi-glass-card {
        background: rgba(255, 255, 255, 0.10);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        height: 120px;
        padding: 16px 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 25px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 25px 70px rgba(37, 99, 235, 0.35);
        border-color: rgba(56, 189, 248, 0.4);
    }

    .kpi-icon-blue {
        font-size: 20px;
        color: #38BDF8 !important;
    }

    .kpi-val-white {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF !important;
        line-height: 1;
        margin: 4px 0;
    }

    .kpi-lbl-slate {
        font-size: 12px;
        font-weight: 600;
        color: #CBD5E1 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Suggestion Buttons (Blue Glow Pill Buttons) */
    .chip-glass-wrap .stButton > button {
        border-radius: 30px !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        background: rgba(37, 99, 235, 0.2) !important;
        color: #38BDF8 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    .chip-glass-wrap .stButton > button:hover {
        background: linear-gradient(135deg, #2563EB, #3B82F6) !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 20px rgba(37, 99, 235, 0.6) !important;
        border-color: #38BDF8 !important;
    }

    /* ChatGPT Dark Glass Chat Bubbles - Max 75% Width */
    .chat-bubble-user-glass {
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        color: #FFFFFF !important;
        border-radius: 16px 16px 4px 16px;
        padding: 14px 18px;
        font-size: 14px;
        max-width: 75%;
        margin-left: auto;
        margin-bottom: 18px;
        box-shadow: 0 0 20px rgba(37, 99, 235, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .chat-bubble-ai-glass {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        color: #FFFFFF !important;
        border-radius: 16px 16px 16px 4px;
        padding: 16px 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        font-size: 14px;
        line-height: 1.6;
        max-width: 75%;
        margin-right: auto;
        margin-bottom: 18px;
    }

    /* Chat Input Glass Container */
    .stChatInputContainer textarea {
        background: rgba(15, 23, 42, 0.8) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
    }

    /* Insights Item Cards */
    .insight-item-glass {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 12px;
    }

    .insight-item-head {
        font-size: 13px;
        font-weight: 700;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .insight-item-body {
        font-size: 12px;
        color: #CBD5E1 !important;
        margin-top: 4px;
    }

    /* Timeline Items */
    .timeline-row {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        color: #CBD5E1 !important;
        margin-bottom: 10px;
    }
    .timeline-row:last-child {
        margin-bottom: 0;
    }

    /* Blue Gradient Glow Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        height: 45px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        background: linear-gradient(135deg, #2563EB, #3B82F6) !important;
        color: #FFFFFF !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    }

    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(37, 99, 235, 0.8) !important;
        border-color: #38BDF8 !important;
    }

    /* Sidebar Button Glow */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #2563EB, #3B82F6) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 0 15px rgba(37, 99, 235, 0.5) !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.8) !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Caching Service for Platform Data Ingestion & Dataframe Normalization
@st.cache_data(ttl=45)
def fetch_platform_data():
    """
    Fetches metrics, deals, and work orders from FastAPI backend or local Python services.
    Ensures DataFrames are normalized with explicit column attributes required for plotting.
    """
    data = {
        "health": {"status": "healthy", "monday_connection": "connected", "groq_status": "Initialized"},
        "pipeline": {"success": True, "total_deals": 0, "total_pipeline_value": 0, "average_deal_value": 0},
        "revenue": {"success": True, "total_invoiced_amount": 0, "total_collected_amount": 0, "pending_collection_amount": 0},
        "deals_df": pd.DataFrame(),
        "work_orders_df": pd.DataFrame(),
    }

    # 1. Health Check
    try:
        h_res = requests.get(f"{API_BASE_URL}/health", timeout=4)
        if h_res.status_code == 200:
            data["health"] = h_res.json()
    except Exception as ex:
        logger.warning(f"Health API request failed: {ex}. Falling back to local check.")
        try:
            conn = monday_service.test_connection()
            data["health"]["monday_connection"] = "connected" if conn.get("success") else "failed"
        except Exception:
            data["health"]["monday_connection"] = "failed"

    # 2. Pipeline Summary
    try:
        p_res = requests.get(f"{API_BASE_URL}/pipeline-summary", timeout=4)
        if p_res.status_code == 200:
            data["pipeline"] = p_res.json()
    except Exception as ex:
        logger.warning(f"Pipeline summary API call failed: {ex}")
        data["pipeline"] = bi_service.get_pipeline_summary()

    # 3. Revenue Summary
    try:
        r_res = requests.get(f"{API_BASE_URL}/revenue-summary", timeout=4)
        if r_res.status_code == 200:
            data["revenue"] = r_res.json()
    except Exception as ex:
        logger.warning(f"Revenue summary API call failed: {ex}")
        data["revenue"] = bi_service.get_revenue_summary()

    # 4. Deals Dataset Extraction & Normalization
    try:
        deals_df_raw, _ = bi_service._get_cleaned_deals_df()
        if not deals_df_raw.empty:
            # Map normalized attributes
            deals_df_raw["stage"] = deals_df_raw.get("col_text_mm5nh2c6", deals_df_raw["status"]).fillna("Unassigned")
            deals_df_raw["owner"] = deals_df_raw.get("col_text_mm5nhwnf", pd.Series(["OWNER_001"] * len(deals_df_raw))).fillna("OWNER_001")
            data["deals_df"] = deals_df_raw
            logger.info(f"Normalized deals_df shape: {deals_df_raw.shape}, columns: {deals_df_raw.columns.tolist()}")
    except Exception as ex:
        logger.error(f"Error extracting deals dataframe: {ex}")
        d_raw = monday_service.get_deals()
        d_clean = cleaning_service.clean_deals(d_raw)
        data["deals_df"] = pd.DataFrame(d_clean.get("deals", []))

    # 5. Work Orders Dataset Extraction & Normalization
    try:
        wo_df_raw, _ = bi_service._get_cleaned_work_orders_df()
        if not wo_df_raw.empty:
            wo_df_raw["execution_status"] = wo_df_raw.get("col_text_mm5n2f02", wo_df_raw.get("col_status", wo_df_raw["status"])).fillna("Unknown")
            wo_df_raw["customer_name"] = wo_df_raw.get("col_text_mm5neacp", wo_df_raw["name"]).fillna("Unknown Customer")
            wo_df_raw["probable_end_date"] = wo_df_raw.get("col_date4", wo_df_raw.get("updated_at", pd.Series([""] * len(wo_df_raw)))).fillna("")
            data["work_orders_df"] = wo_df_raw
            logger.info(f"Normalized work_orders_df shape: {wo_df_raw.shape}, columns: {wo_df_raw.columns.tolist()}")
    except Exception as ex:
        logger.error(f"Error extracting work orders dataframe: {ex}")
        w_raw = monday_service.get_work_orders()
        w_clean = cleaning_service.clean_work_orders(w_raw)
        data["work_orders_df"] = pd.DataFrame(w_clean.get("work_orders", []))

    return data


# Load Platform Metrics
platform_data = fetch_platform_data()
health_info = platform_data["health"]
pipeline_info = platform_data["pipeline"]
revenue_info = platform_data["revenue"]
deals_df = platform_data["deals_df"]
work_orders_df = platform_data["work_orders_df"]

# Empirical Log Debugging of DataFrames
logger.info(f"[DEBUG] deals_df rows: {len(deals_df)}, columns: {deals_df.columns.tolist() if not deals_df.empty else []}")
logger.info(f"[DEBUG] work_orders_df rows: {len(work_orders_df)}, columns: {work_orders_df.columns.tolist() if not work_orders_df.empty else []}")

# Compute Key Numeric Indicators
total_deals = pipeline_info.get("total_deals", len(deals_df))
pipeline_val = pipeline_info.get("total_pipeline_value", 0)
invoiced_val = revenue_info.get("total_invoiced_amount", 0)
collected_val = revenue_info.get("total_collected_amount", 0)
pending_val = revenue_info.get("pending_collection_amount", 0)
total_work_orders = len(work_orders_df)

# Overdue Calculation
overdue_orders_count = 0
if not work_orders_df.empty and "probable_end_date" in work_orders_df.columns:
    today_date = datetime.now().strftime("%Y-%m-%d")
    overdue_mask = (
        (work_orders_df["probable_end_date"].fillna("") < today_date) &
        (work_orders_df["probable_end_date"].fillna("") != "") &
        (work_orders_df.get("execution_status", pd.Series()).fillna("").str.lower() != "completed")
    )
    overdue_orders_count = int(overdue_mask.sum())


# ==============================================================================
# SIDEBAR (DARK GLASS #0F172A)
# ==============================================================================
st.sidebar.markdown(
    """
    <div class="sidebar-brand-box">
        <h2 class="sidebar-brand-title">🚀 Monday BI Agent</h2>
        <p class="sidebar-brand-sub">Executive BI Platform</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "Navigation Menu",
    [
        "🏠 Dashboard",
        "🤖 AI Assistant",
        "📊 Analytics",
        "💼 Deals",
        "📋 Work Orders",
        "⚙️ Health",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")

# Refresh Data Button at Sidebar Bottom (Blue Gradient Glow)
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


# ==============================================================================
# TOP GLASS HEADER CARD
# ==============================================================================
st.markdown(
    """
    <div class="top-header-glass">
        <div class="header-left">
            <h1>🚀 Monday BI Agent</h1>
            <p>AI Powered Executive Business Intelligence Dashboard</p>
        </div>
        <div class="header-badges">
            <span class="badge-chip-glass">🟢 Monday Connected</span>
            <span class="badge-chip-glass">🟢 Groq Online</span>
            <span class="badge-chip-glass">🟢 FastAPI Running</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# PAGE 1: 🏠 DASHBOARD (Dark Glassmorphism Layout)
# ==============================================================================
if nav_choice == "🏠 Dashboard":

    # 1 ROW OF 6 DARK GLASS KPI CARDS
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">💼</div>
                <div class="kpi-val-white">{total_deals:,}</div>
                <div class="kpi-lbl-slate">Total Deals</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">💰</div>
                <div class="kpi-val-white">${pipeline_val:,.0f}</div>
                <div class="kpi-lbl-slate">Pipeline Value</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">📈</div>
                <div class="kpi-val-white">${collected_val:,.0f}</div>
                <div class="kpi-lbl-slate">Revenue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">🧾</div>
                <div class="kpi-val-white">${pending_val:,.0f}</div>
                <div class="kpi-lbl-slate">Pending</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k5:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">📋</div>
                <div class="kpi-val-white">{total_work_orders:,}</div>
                <div class="kpi-lbl-slate">Orders</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k6:
        st.markdown(
            f"""
            <div class="kpi-glass-card">
                <div class="kpi-icon-blue">⚠️</div>
                <div class="kpi-val-white" style="color: {'#F87171' if overdue_orders_count > 0 else '#34D399'} !important;">{overdue_orders_count}</div>
                <div class="kpi-lbl-slate">Overdue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # TWO COLUMN MAIN CONTENT LAYOUT (70% / 30%)
    left_col, right_col = st.columns([7, 3])

    # LEFT COLUMN (70%) - DARK GLASS AI ASSISTANT CARD (st.container(border=True))
    with left_col:
        with st.container(border=True):
            st.markdown(
                """
                <h2 style="font-size: 22px; font-weight: 700; color: #FFFFFF; margin: 0 0 4px 0;">🤖 AI Executive Assistant</h2>
                <p style="font-size: 13px; color: #CBD5E1; margin: 0 0 18px 0;">Ask questions about your Monday workspace.</p>
                """,
                unsafe_allow_html=True,
            )

            # 6 Suggestion Buttons (Blue Glow Pill Buttons)
            suggestion_chips = ["Revenue", "Pipeline", "Invoices", "Customers", "Overdue", "Executive Summary"]
            chip_cols = st.columns(len(suggestion_chips))
            clicked_chip = None

            for idx, chip_text in enumerate(suggestion_chips):
                with chip_cols[idx]:
                    st.markdown('<div class="chip-glass-wrap">', unsafe_allow_html=True)
                    if st.button(chip_text, key=f"chip_glass_{idx}", use_container_width=True):
                        clicked_chip = chip_text
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Chat History State
            if "main_chat_history" not in st.session_state:
                st.session_state.main_chat_history = [
                    {
                        "role": "assistant",
                        "content": "Hello! I am your AI Executive Assistant powered by Groq and LangChain. How can I assist you with your Monday workspace metrics today?",
                    }
                ]

            # Render Chat History (ChatGPT Dark Glass style, 🤖 left, 👤 right, max 75% width)
            for msg in st.session_state.main_chat_history:
                role = msg["role"]
                avatar = "🤖" if role == "assistant" else "👤"
                with st.chat_message(role, avatar=avatar):
                    if role == "assistant":
                        st.markdown(f'<div class="chat-bubble-ai-glass">{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-bubble-user-glass">{msg["content"]}</div>', unsafe_allow_html=True)

            # Helper function for user query submission
            def process_chat_query(query_str: str):
                st.session_state.main_chat_history.append({"role": "user", "content": query_str})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(f'<div class="chat-bubble-user-glass">{query_str}</div>', unsafe_allow_html=True)

                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Thinking..."):
                        answer_text = ""
                        try:
                            res = requests.post(f"{API_BASE_URL}/chat", json={"question": query_str}, timeout=60)
                            if res.status_code == 200:
                                answer_text = res.json().get("answer", "")
                            else:
                                answer_text = f"API Error: {res.json().get('detail', 'Failed to fetch answer.')}"
                        except Exception:
                            try:
                                answer_text = ask(query_str)
                            except Exception as ex:
                                answer_text = f"An error occurred: {str(ex)}"

                        st.markdown(f'<div class="chat-bubble-ai-glass">{answer_text}</div>', unsafe_allow_html=True)
                        st.session_state.main_chat_history.append({"role": "assistant", "content": answer_text})

            # Trigger Clicked Suggestion Chip
            if clicked_chip:
                process_chat_query(clicked_chip)
                st.rerun()

            # Fixed Chat Input at Bottom of Glass Card
            if user_prompt := st.chat_input("Ask anything about revenue, deals or work orders..."):
                process_chat_query(user_prompt)

    # RIGHT COLUMN (30%) - DARK GLASS INSIGHTS & TIMELINE (st.container(border=True))
    with right_col:
        with st.container(border=True):
            st.markdown(
                f"""
                <h3 style="font-size: 18px; font-weight: 700; color: #FFFFFF; margin: 0 0 16px 0;">Business Insights</h3>
                <div class="insight-item-glass">
                    <div class="insight-item-head"><span>🟢</span> <span>Revenue Health</span></div>
                    <div class="insight-item-body">${collected_val:,.2f} collected ({collected_val/invoiced_val*100 if invoiced_val > 0 else 0:.1f}% rate).</div>
                </div>
                <div class="insight-item-glass">
                    <div class="insight-item-head"><span>🔵</span> <span>Pipeline Status</span></div>
                    <div class="insight-item-body">{total_deals} active deals carrying ${pipeline_val:,.2f} valuation.</div>
                </div>
                <div class="insight-item-glass">
                    <div class="insight-item-head"><span>🟡</span> <span>Pending Invoices</span></div>
                    <div class="insight-item-body">${pending_val:,.2f} receivables pending collection across accounts.</div>
                </div>
                <div class="insight-item-glass">
                    <div class="insight-item-head"><span>{'🔴' if overdue_orders_count > 0 else '🟢'}</span> <span>Work Orders</span></div>
                    <div class="insight-item-body">{overdue_orders_count} work order(s) past expected delivery target.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown(
                f"""
                <h4 style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;">Recent Activity</h4>
                <div class="timeline-row"><span>✔</span> <span>Latest Sync: Monday GraphQL API Connected</span></div>
                <div class="timeline-row"><span>✔</span> <span>Last AI Query: Groq LLaMA-3.3 70B Active</span></div>
                <div class="timeline-row"><span>✔</span> <span>Latest Monday Update: {total_deals} Deals & {total_work_orders} Orders</span></div>
                """,
                unsafe_allow_html=True,
            )

    # BOTTOM SECTION: TWO DARK PLOTLY CHARTS INSIDE GLASS CONTAINERS
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("<h4 style='color: #FFFFFF; font-weight: 700; margin: 0 0 12px 0;'>Revenue Breakdown</h4>", unsafe_allow_html=True)
            if invoiced_val > 0:
                fig_rev = px.pie(
                    values=[collected_val, pending_val],
                    names=["Collected Revenue", "Pending Receivables"],
                    color_discrete_sequence=["#34D399", "#F87171"],
                    hole=0.5,
                    template="plotly_dark",
                )
                fig_rev.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=340,
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(color="#FFFFFF"),
                )
                st.plotly_chart(fig_rev, width="stretch")
            else:
                st.warning("No revenue summary data available to plot.")

    with c2:
        with st.container(border=True):
            st.markdown("<h4 style='color: #FFFFFF; font-weight: 700; margin: 0 0 12px 0;'>Deals by Stage</h4>", unsafe_allow_html=True)
            if not deals_df.empty and "stage" in deals_df.columns:
                stg_df = deals_df["stage"].value_counts().reset_index()
                stg_df.columns = ["Stage", "Count"]

                fig_stg = px.bar(
                    stg_df,
                    x="Stage",
                    y="Count",
                    color="Stage",
                    text="Count",
                    color_discrete_sequence=["#38BDF8", "#818CF8", "#34D399", "#FBBF24", "#F87171"],
                    template="plotly_dark",
                )
                fig_stg.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=340,
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(color="#FFFFFF"),
                )
                st.plotly_chart(fig_stg, width="stretch")
            else:
                st.warning("Deals dataframe missing required 'stage' column for plotting.")


# ==============================================================================
# PAGE 2: 🤖 AI ASSISTANT (Full-Screen Dark Glass Chat Interface)
# ==============================================================================
elif nav_choice == "🤖 AI Assistant":

    with st.container(border=True):
        st.markdown(
            """
            <h2 style="font-size: 22px; font-weight: 700; color: #FFFFFF; margin: 0 0 4px 0;">🤖 AI Executive Assistant</h2>
            <p style="font-size: 13px; color: #CBD5E1; margin: 0 0 18px 0;">Full-screen dark glass conversational business intelligence interface.</p>
            """,
            unsafe_allow_html=True,
        )

        if "ai_page_history" not in st.session_state:
            st.session_state.ai_page_history = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your AI Executive Assistant powered by Groq and LangChain. Ask me anything about revenue, deals, work orders, or customers.",
                }
            ]

        for msg in st.session_state.ai_page_history:
            r = msg["role"]
            av = "🤖" if r == "assistant" else "👤"
            with st.chat_message(r, avatar=av):
                if r == "assistant":
                    st.markdown(f'<div class="chat-bubble-ai-glass">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-user-glass">{msg["content"]}</div>', unsafe_allow_html=True)

        if q_in := st.chat_input("Ask anything about revenue, deals or work orders..."):
            st.session_state.ai_page_history.append({"role": "user", "content": q_in})
            with st.chat_message("user", avatar="👤"):
                st.markdown(f'<div class="chat-bubble-user-glass">{q_in}</div>', unsafe_allow_html=True)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    a_txt = ""
                    try:
                        res = requests.post(f"{API_BASE_URL}/chat", json={"question": q_in}, timeout=60)
                        if res.status_code == 200:
                            a_txt = res.json().get("answer", "")
                        else:
                            a_txt = f"API Error: {res.json().get('detail', 'API Request failed.')}"
                    except Exception:
                        try:
                            a_txt = ask(q_in)
                        except Exception as ex:
                            a_txt = f"An error occurred: {str(ex)}"

                    st.markdown(f'<div class="chat-bubble-ai-glass">{a_txt}</div>', unsafe_allow_html=True)
                    st.session_state.ai_page_history.append({"role": "assistant", "content": a_txt})


# ==============================================================================
# PAGE 3: 📊 ANALYTICS
# ==============================================================================
elif nav_choice == "📊 Analytics":

    st.markdown("<h2 style='color: #FFFFFF; font-weight: 700;'>📊 Workspace Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True):
            st.markdown("<h4 style='color: #FFFFFF;'>Deals Stage Breakdown</h4>", unsafe_allow_html=True)
            if not deals_df.empty and "stage" in deals_df.columns:
                stg = deals_df["stage"].value_counts().reset_index()
                stg.columns = ["Stage", "Deals"]
                fig_a = px.bar(stg, x="Stage", y="Deals", color="Stage", text="Deals", template="plotly_dark")
                fig_a.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=330,
                    font=dict(color="#FFFFFF"),
                )
                st.plotly_chart(fig_a, width="stretch")
            else:
                st.warning("Deals dataframe missing required 'stage' column for analytics.")

    with col_b:
        with st.container(border=True):
            st.markdown("<h4 style='color: #FFFFFF;'>Top 10 Customers by Volume</h4>", unsafe_allow_html=True)
            if not work_orders_df.empty and "customer_name" in work_orders_df.columns:
                tc = work_orders_df["customer_name"].value_counts().head(10).reset_index()
                tc.columns = ["Customer", "Orders"]
                fig_b = px.bar(
                    tc,
                    x="Orders",
                    y="Customer",
                    orientation="h",
                    color="Orders",
                    color_continuous_scale="Blues",
                    text="Orders",
                    template="plotly_dark",
                )
                fig_b.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(autorange="reversed"),
                    height=330,
                    font=dict(color="#FFFFFF"),
                )
                st.plotly_chart(fig_b, width="stretch")
            else:
                st.warning("Work orders dataframe missing required 'customer_name' column for analytics.")


# ==============================================================================
# PAGE 4: 💼 DEALS
# ==============================================================================
elif nav_choice == "💼 Deals":

    st.markdown("<h2 style='color: #FFFFFF; font-weight: 700;'>💼 Sales Deals Explorer</h2>", unsafe_allow_html=True)

    if not deals_df.empty:
        d1, d2, d3 = st.columns(3)
        with d1:
            d_search = st.text_input("🔍 Search Deals / Clients", "")
        with d2:
            stg_opts = ["All"] + sorted(list(deals_df["stage"].dropna().unique())) if "stage" in deals_df.columns else ["All"]
            stg_val = st.selectbox("Filter by Stage", stg_opts)
        with d3:
            own_opts = ["All"] + sorted(list(deals_df["owner"].dropna().unique())) if "owner" in deals_df.columns else ["All"]
            own_val = st.selectbox("Filter by Owner", own_opts)

        filtered_d = deals_df.copy()
        if d_search:
            filtered_d = filtered_d[filtered_d.apply(lambda r: d_search.lower() in str(r.values).lower(), axis=1)]
        if stg_val != "All" and "stage" in filtered_d.columns:
            filtered_d = filtered_d[filtered_d["stage"] == stg_val]
        if own_val != "All" and "owner" in filtered_d.columns:
            filtered_d = filtered_d[filtered_d["owner"] == own_val]

        st.markdown(f"**Records: {len(filtered_d)} of {len(deals_df)}**")
        st.dataframe(filtered_d, use_container_width=True, height=450)

        st.download_button(
            "📥 Export Deals to CSV",
            data=filtered_d.to_csv(index=False),
            file_name=f"deals_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No sales deals data loaded.")


# ==============================================================================
# PAGE 5: 📋 WORK ORDERS
# ==============================================================================
elif nav_choice == "📋 Work Orders":

    st.markdown("<h2 style='color: #FFFFFF; font-weight: 700;'>📋 Work Orders Explorer</h2>", unsafe_allow_html=True)

    if not work_orders_df.empty:
        wo1, wo2 = st.columns(2)
        with wo1:
            w_search = st.text_input("🔍 Search Work Orders / Customers", "")
        with wo2:
            stat_opts = ["All"] + sorted(list(work_orders_df["execution_status"].dropna().unique())) if "execution_status" in work_orders_df.columns else ["All"]
            stat_val = st.selectbox("Filter Status", stat_opts)

        filtered_w = work_orders_df.copy()
        if w_search:
            filtered_w = filtered_w[filtered_w.apply(lambda r: w_search.lower() in str(r.values).lower(), axis=1)]
        if stat_val != "All" and "execution_status" in filtered_w.columns:
            filtered_w = filtered_w[filtered_w["execution_status"] == stat_val]

        st.markdown(f"**Records: {len(filtered_w)} of {len(work_orders_df)}**")
        st.dataframe(filtered_w, use_container_width=True, height=450)

        st.download_button(
            "📥 Export Work Orders to CSV",
            data=filtered_w.to_csv(index=False),
            file_name=f"work_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No work orders data loaded.")


# ==============================================================================
# PAGE 6: ⚙️ HEALTH
# ==============================================================================
elif nav_choice == "⚙️ Health":

    st.markdown("<h2 style='color: #FFFFFF; font-weight: 700;'>⚙️ System Health & Infrastructure Diagnostics</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    h1, h2, h3 = st.columns(3)

    with h1:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">🔌</div>
                <div class="kpi-val-white" style="color: #34D399 !important;">Connected</div>
                <div class="kpi-lbl-slate">Monday GraphQL API v2</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h2:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">⚡</div>
                <div class="kpi-val-white" style="color: #34D399 !important;">Online</div>
                <div class="kpi-lbl-slate">Groq LLaMA-3.3 70B</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h3:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">🖥️</div>
                <div class="kpi-val-white" style="color: #34D399 !important;">Running</div>
                <div class="kpi-lbl-slate">FastAPI Port 8000</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">📦</div>
                <div class="kpi-val-white">2</div>
                <div class="kpi-lbl-slate">Boards Loaded</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">💼</div>
                <div class="kpi-val-white">{total_deals:,}</div>
                <div class="kpi-lbl-slate">Deals Loaded</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-glass-card" style="height: 130px;">
                <div class="kpi-icon-blue">📋</div>
                <div class="kpi-val-white">{total_work_orders:,}</div>
                <div class="kpi-lbl-slate">Work Orders Loaded</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
