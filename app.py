import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------------------------------
# Page config & BEAUTIFICATION (Light Blue & Orange)
# -------------------------------------------------
st.set_page_config(
    page_title="Fedus Master Price List",
    layout="wide",
    page_icon="🔌"
)

# ULTIMATE STICKY CSS
st.markdown("""
    <style>
    /* Fedus Branding */
    .stApp { background-color: #F0F8FF; }
    h1 { color: #FF8C00 !important; font-weight: 800; }
    section[data-testid="stSidebar"] {
        background-color: #E6F3FF !important;
        border-right: 3px solid #FFCC80;
    }

    /* THE STICKY TABLE LOGIC */
    .sticky-table-container {
        overflow-x: auto;
        max-width: 100%;
        border: 1px solid #FFCC80;
        border-radius: 10px;
        background-color: white;
    }

    table {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
    }

    /* Pinned Columns: ASIN, Preview, Title (Columns 2, 3, 4) */
    /* SI No (Col 1) is also pinned for context */
    th:nth-child(1), td:nth-child(1),
    th:nth-child(2), td:nth-child(2),
    th:nth-child(3), td:nth-child(3),
    th:nth-child(4), td:nth-child(4) {
        position: sticky !important;
        left: 0;
        z-index: 3;
        background-color: white !important;
        border-right: 1px solid #FFCC80 !important;
    }

    /* Setting specific offsets so they don't overlap each other */
    th:nth-child(2), td:nth-child(2) { left: 50px; }  /* Adjust based on SI No width */
    th:nth-child(3), td:nth-child(3) { left: 150px; } /* Adjust based on ASIN width */
    th:nth-child(4), td:nth-child(4) { left: 230px; } /* Adjust based on Preview width */

    /* Header Stability */
    th {
        position: sticky !important;
        top: 0;
        z-index: 4;
        background-color: #FFCC80 !important;
        color: #333;
    }

    /* Hover effect for full name */
    td:nth-child(4):hover::after {
        content: attr(data-fulltext);
        position: absolute;
        background: #333;
        color: #fff;
        padding: 8px;
        border-radius: 4px;
        width: 250px;
        white-space: normal;
        z-index: 10;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔌 Fedus Master Price List")

# -------------------------------------------------
# Robust Data Loading (Logic Unchanged)
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
        # skiprows=1 skips the blue Row 1
        sheets = pd.read_excel(BytesIO(r.content), sheet_name=None, engine="openpyxl", skiprows=1)
    return {name: df for name, df in sheets.items() if df is not None and not df.empty}

with st.spinner("Syncing Fedus Master Data..."):
    try:
        sheets = load_all_sheets(XLSX_URL)
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        st.stop()

# -------------------------------------------------
# Sidebar & Search
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
# RENDERING THE HTML TABLE (Zero-Failure Sticky)
# -----------------------------------------------
# We convert the dataframe to HTML to apply our custom Sticky CSS
def make_html_table(df):
    # Shorten titles for the view but keep full text for hover
    if 'Title' in df.columns:
        df['Title_Display'] = df['Title'].apply(lambda x: (str(x)[:30] + '...') if len(str(x)) > 30 else x)
    
    html = df.to_html(classes='fedus-table', index=False, escape=False)
    return f'<div class="sticky-table-container">{html}</div>'

st.markdown(f"Rows found: **{len(display_df):,}**")
st.markdown(make_html_table(display_df), unsafe_allow_html=True)
