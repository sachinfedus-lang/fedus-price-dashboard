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

# Custom CSS for Fedus Branding
st.markdown("""
    <style>
    /* Main Background and Text */
    .stApp {
        background-color: #f0f8ff; /* Light Alice Blue */
    }
    
    /* Header Styling */
    h1 {
        color: #ff8c00; /* Dark Orange */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #e6f3ff; /* Light Sky Blue */
        border-right: 2px solid #ffcc80; /* Light Orange Border */
    }
    
    /* Custom tooltips for long titles */
    [data-testid="stDataFrame"] td:hover {
        cursor: help;
    }
    
    /* Search box styling */
    .stTextInput>div>div>input {
        border: 2px solid #ffcc80;
    }
    </style>
    """, unsafe_allow_index=True)

st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | <span style='color: #ff8c00;'>Updated Live</span>", unsafe_allow_index=True)

# -------------------------------------------------
# Published XLSX URL (entire document)
# -------------------------------------------------
XLSX_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w"
    "/pub?output=xlsx"
)

# -------------------------------------------------
# Robust downloader with retry + streaming (LOGIC UNCHANGED)
# -------------------------------------------------
@st.cache_data(ttl=600)
def download_xlsx_streaming(url: str) -> bytes:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"User-Agent": "Mozilla/5.0"}
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        buffer = BytesIO()
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                buffer.write(chunk)
        return buffer.getvalue()

# -------------------------------------------------
# Load all sheets safely (Logic preserved + skiprows for headers)
# -------------------------------------------------
@st.cache_data(ttl=600)
def load_all_sheets(url: str):
    raw_bytes = download_xlsx_streaming(url)
    sheets = pd.read_excel(
        BytesIO(raw_bytes),
        sheet_name=None,
        engine="openpyxl",
        skiprows=1 # Skips the blue bar to keep headers visible
    )
    clean = {
        name: df
        for name, df in sheets.items()
        if df is not None and not df.empty and len(df.columns) > 0
    }
    if not clean:
        raise RuntimeError("All sheets were empty or unreadable.")
    return clean

# -------------------------------------------------
# Fetch data
# -------------------------------------------------
with st.spinner("Syncing all Fedus categories..."):
    try:
        sheets = load_all_sheets(XLSX_URL)
    except Exception as e:
        st.error(f"❌ Error loading workbook: {e}")
        st.stop()

sheet_names = list(sheets.keys())

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("Navigation")
selected_sheet = st.sidebar.selectbox("📂 Select Category", sheet_names)
global_search = st.sidebar.checkbox("🔍 Search across ALL categories")

search_query = st.text_input(
    "🔍 Search products",
    placeholder="Type here to search (e.g. Cat 6, Blue...)"
)

def search_df(df, query):
    if not query:
        return df
    return df[
        df.astype(str)
        .apply(lambda r: r.str.contains(query, case=False, na=False))
        .any(axis=1)
    ]

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

# Display Row Count with orange highlight
st.markdown(f"Rows found: **<span style='color: #ff8c00;'>{len(display_df):,}</span>**", unsafe_allow_index=True)

# -----------------------------------------------
# Column configuration (Tooltips and Static Headers)
# -----------------------------------------------
column_config = {
    # This configuration helps with cell width and tooltips
    "Title": st.column_config.TextColumn(
        "Title",
        help="Hover to see the full product title",
        width="large"
    )
}

if "Image" in display_df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview")

if "PRODUCT Gallery" in display_df.columns:
    column_config["PRODUCT Gallery"] = st.column_config.LinkColumn(
        "Gallery", display_text="Open"
    )

# The dataframe with pinned headers (standard in current Streamlit)
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config
)
