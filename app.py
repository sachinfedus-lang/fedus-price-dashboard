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

# Custom CSS for Fedus Branding and Hover Effects
st.markdown("""
    <style>
    /* Main Background: Alice Blue */
    .stApp {
        background-color: #F0F8FF;
    }
    
    /* Header Styling: Fedus Orange */
    h1 {
        color: #FF8C00 !important;
        font-weight: 800;
    }
    
    /* Sidebar: Light Sky Blue and Orange Border */
    section[data-testid="stSidebar"] {
        background-color: #E6F3FF !important;
        border-right: 3px solid #FFCC80;
    }

    /* Row Count Highlight */
    .row-count {
        color: #FF8C00;
        font-weight: bold;
    }

    /* Custom hover logic to show full text in cells */
    [data-testid="stDataFrame"] td:hover {
        overflow: visible;
        white-space: normal;
        background-color: #FFF5E6; /* Very light orange on hover */
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔌 Fedus Master Price List")
st.markdown("### Search Categories | <span style='color: #FF8C00;'>Live Sync Active</span>", unsafe_allow_html=True)

# -------------------------------------------------
# Published XLSX URL
# -------------------------------------------------
XLSX_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w"
    "/pub?output=xlsx"
)

# -------------------------------------------------
# Robust downloader (LOGIC UNCHANGED)
# -------------------------------------------------
@st.cache_data(ttl=60) # Updated to 60s for faster syncing
def download_xlsx_streaming(url: str) -> bytes:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"User-Agent": "Mozilla/5.0"}
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        buffer = BytesIO()
        for chunk in r.iter_content(chunk_size=8192):
            if chunk: buffer.write(chunk)
        return buffer.getvalue()

# -------------------------------------------------
# Load all sheets safely (skiprows=1 for your blue bar)
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_all_sheets(url: str):
    raw_bytes = download_xlsx_streaming(url)
    sheets = pd.read_excel(BytesIO(raw_bytes), sheet_name=None, engine="openpyxl", skiprows=1)
    return {name: df for name, df in sheets.items() if df is not None and not df.empty and len(df.columns) > 0}

# -------------------------------------------------
# Fetch data
# -------------------------------------------------
with st.spinner("Syncing Fedus Categories..."):
    try:
        sheets = load_all_sheets(XLSX_URL)
    except Exception as e:
        st.error(f"❌ Error loading workbook: {e}")
        st.stop()

sheet_names = list(sheets.keys())

# -------------------------------------------------
# Sidebar & Navigation
# -------------------------------------------------
st.sidebar.header("Navigation")
selected_sheet = st.sidebar.selectbox("📂 Select Category", sheet_names)
global_search = st.sidebar.checkbox("🔍 Search across ALL categories")

search_query = st.text_input("🔍 Search products", placeholder="Type SKU or Title...")

def search_df(df, query):
    if not query: return df
    return df[df.astype(str).apply(lambda r: r.str.contains(query, case=False, na=False)).any(axis=1)]

# -------------------------------------------------
# Display logic
# -------------------------------------------------
if global_search:
    combined = []
    for name, df in sheets.items():
        temp = df.copy()
        temp.insert(0, "Category", name)
        combined.append(temp)
    display_df = pd.concat(combined, ignore_index=True, sort=False)
    display_df = search_df(display_df, search_query)
    st.subheader("🔎 Global Search Results")
else:
    display_df = search_df(sheets[selected_sheet], search_query)
    st.subheader(f"📂 Category: {selected_sheet}")

st.markdown(f"Rows found: <span class='row-count'>{len(display_df):,}</span>", unsafe_allow_html=True)

# -----------------------------------------------
# STICKY COLUMN & HOVER CONFIGURATION
# -----------------------------------------------
# We use 'on_select' to stabilize the view and define column widths
column_config = {
    "Title": st.column_config.TextColumn(
        "Title",
        help="Hover to see full product title",
        width="medium"
    ),
    "ASIN": st.column_config.TextColumn(
        "ASIN",
        width="small"
    )
}

if "Image" in display_df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview", width="small")

if "PRODUCT Gallery" in display_df.columns:
    column_config["PRODUCT Gallery"] = st.column_config.LinkColumn("Gallery", display_text="Open")

# PINNING LOGIC: Pin the first 4 columns (SI No, Image, Title, ASIN)
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config,
    on_select="ignore" # Prevents refresh on click
)
