import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------------------------------
# Page config & BEAUTIFICATION
# -------------------------------------------------
st.set_page_config(
    page_title="Fedus Master Price List",
    layout="wide",
    page_icon="🔌"
)

st.markdown("""
    <style>
    .stApp { background-color: #F0F8FF; }
    h1 { color: #FF8C00 !important; font-weight: 800; margin-bottom: 20px; }
    .category-header {
        color: #FF8C00; font-size: 24px; font-weight: 600;
        background-color: #ffffff; padding: 10px 20px;
        border-radius: 10px; border-left: 5px solid #FF8C00;
        margin-top: 20px; margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] {
        background-color: #E6F3FF !important;
        border-right: 3px solid #FFCC80;
    }
    [data-testid="stDataFrame"] thead tr th {
        background-color: #FFCC80 !important;
        color: #333 !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR LOGO
# -------------------------------------------------
try:
    st.sidebar.image("fedus-logo.png", use_container_width=True)
except:
    st.sidebar.markdown("### 🔌 Master Price List")

# -------------------------------------------------
# DATA LOADING (ORDER PRESERVED)
# -------------------------------------------------
XLSX_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w/pub?output=xlsx"

@st.cache_data(ttl=60)
def load_all_sheets(url: str):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"User-Agent": "Mozilla/5.0"}
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        # Maintains Excel tab order
        return pd.read_excel(BytesIO(r.content), sheet_name=None, engine="openpyxl", skiprows=1)

with st.spinner("Syncing..."):
    try:
        raw_sheets = load_all_sheets(XLSX_URL)
        sheets = {name: df for name, df in raw_sheets.items() if df is not None and not df.empty}
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.stop()

# -------------------------------------------------
# NAVIGATION (Fixed Order)
# -------------------------------------------------
sheet_names = list(sheets.keys())
st.sidebar.header("Navigation")
selected_sheet = st.sidebar.selectbox("📂 Select Category", sheet_names, index=0)
global_search = st.sidebar.checkbox("🔍 Search across ALL categories")

# -------------------------------------------------
# MAIN UI
# -------------------------------------------------
st.title("Master Price List")
search_query = st.text_input("🔍 Search products", placeholder="Type SKU or Title...")

if global_search:
    st.markdown('<div class="category-header">🔎 Global Search Results</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="category-header">📂 Category: {selected_sheet}</div>', unsafe_allow_html=True)

# -------------------------------------------------
# PROCESSING & DRIVE LINK LOGIC
# -------------------------------------------------
def search_df(df, query):
    if not query: return df
    return df[df.astype(str).apply(lambda r: r.str.contains(query, case=False, na=False)).any(axis=1)]

if global_search:
    combined = [df.assign(Category=name) for name, df in sheets.items()]
    display_df = search_df(pd.concat(combined, ignore_index=True), search_query)
else:
    display_df = search_df(sheets[selected_sheet], search_query)

# DRIVE LINK DETECTION
column_config = {
    "Title": st.column_config.TextColumn("Title", width="medium", pinned=True, help="Hover for full name"),
    "ASIN": st.column_config.TextColumn("ASIN", width="small", pinned=True)
}

if "Image" in display_df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview", width="small", pinned=True)

# Scan for ANY column with Drive links
for col in display_df.columns:
    sample = str(display_df[col].dropna().iloc[0]) if not display_df[col].dropna().empty else ""
    if "http" in sample or "drive.google" in sample.lower():
        column_config[col] = st.column_config.LinkColumn(col, display_text="Open Link 🔗")

st.write(f"Rows found: **{len(display_df):,}**")
st.dataframe(display_df, use_container_width=True, hide_index=True, column_config=column_config)
