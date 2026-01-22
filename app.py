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
    /* Light Blue Background */
    .stApp { background-color: #F0F8FF; }
    
    /* Orange Headers */
    h1, h3 { color: #FF8C00 !important; }
    
    /* Light Sky Blue Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #E6F3FF !important;
        border-right: 2px solid #FFCC80;
    }

    /* Tooltip behavior for better visibility */
    div[data-testid="stDataFrame"] td {
        cursor: help;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔌 Fedus Master Price List")
st.markdown("### Master Dashboard | <span style='color: #FF8C00;'>Live Sync Active</span>", unsafe_allow_html=True)

# -------------------------------------------------
# Data Loading (TTL updated to 60 seconds)
# -------------------------------------------------
XLSX_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w/pub?output=xlsx"

@st.cache_data(ttl=60) # Syncs changes from Google Sheets every 1 minute
def load_all_sheets(url: str):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"User-Agent": "Mozilla/5.0"}
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        # skiprows=1 skips blue bar to keep 'Title' etc as fixed headers
        sheets = pd.read_excel(BytesIO(r.content), sheet_name=None, engine="openpyxl", skiprows=1)
    return {name: df for name, df in sheets.items() if df is not None and not df.empty}

with st.spinner("Fetching latest prices..."):
    try:
        sheets = load_all_sheets(XLSX_URL)
    except Exception as e:
        st.error(f"❌ Sync Error: {e}")
        st.stop()

# -------------------------------------------------
# Navigation & Search
# -------------------------------------------------
sheet_names = list(sheets.keys())
selected_sheet = st.sidebar.selectbox("📂 Category", sheet_names)
global_search = st.sidebar.checkbox("🔍 Global Search")
search_query = st.text_input("🔍 Search products", placeholder="Type SKU or Title...")

def search_df(df, query):
    if not query: return df
    return df[df.astype(str).apply(lambda r: r.str.contains(query, case=False, na=False)).any(axis=1)]

if global_search:
    combined = []
    for name, df in sheets.items():
        temp = df.copy()
        temp.insert(0, "Category", name)
        combined.append(temp)
    display_df = search_df(pd.concat(combined, ignore_index=True, sort=False), search_query)
else:
    display_df = search_df(sheets[selected_sheet], search_query)

# -----------------------------------------------
# STICKY COLUMN CONFIGURATION
# -----------------------------------------------
column_config = {
    "Title": st.column_config.TextColumn(
        "Title",
        help="Full product name (Sticky)", 
        width="medium",
        required=True
    )
}

if "Image" in display_df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview", width="small")

if "PRODUCT Gallery" in display_df.columns:
    column_config["PRODUCT Gallery"] = st.column_config.LinkColumn("Gallery", display_text="Open", width="small")

# Using the native dataframe with Pinned (Sticky) Title
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config,
    on_select="ignore" # Keeps interface stable during scrolling
)
