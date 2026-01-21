import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ---------------------------
# Page configuration
# ---------------------------
st.set_page_config(
    page_title="Fedus Master Price List",
    layout="wide",
    page_icon="🔌"
)

st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# ---------------------------
# Google Sheet configuration
# ---------------------------
SHEET_ID = "1yccQUPQh8X_JZg8W8BeJQHZVPan6zb1c"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# ---------------------------
# Data loader
# ---------------------------
@st.cache_data(ttl=600)
def load_all_sheets():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=30)

    if response.status_code == 200:
        return pd.read_excel(
            BytesIO(response.content),
            sheet_name=None,
            engine="openpyxl",
            skiprows=1
        )
    elif response.status_code == 401:
        st.error("❌ Google Sheet access denied (401). Make sure the sheet is PUBLIC.")
        return None
    else:
        st.error(f"❌ Failed to download sheet. Status code: {response.status_code}")
        return None

# ---------------------------
# Main app
# ---------------------------
with st.spinner("Syncing all 25+ Fedus categories..."):
    all_sheets = load_all_sheets()

if not all_sheets:
    st.stop()

sheet_names = list(all_sheets.keys())

# Sidebar
st.sidebar.header("Navigation")
selected_sheet = st.sidebar.selectbox("📂 Select Category", sheet_names)

df = all_sheets[selected_sheet]

# Search
search_query = st.text_input(
    f"🔍 Search in {selected_sheet}...",
    placeholder="Search product name, title, SKU, etc."
)

if search_query:
    df = df[df.astype(str).apply(
        lambda row: row.str.contains(search_query, case=False, na=False)
    ).any(axis=1)]

# ---------------------------
# Display table safely
# ---------------------------
column_config = {}

if "Image" in df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview")

if "PRODUCT Gallery" in df.columns:
    column_config["PRODUCT Gallery"] = st.column_config.LinkColumn(
        "Gallery",
        display_text="Open Gallery"
    )

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config if column_config else None
)

