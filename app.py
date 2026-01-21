import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# -----------------------------------------------
# Page configuration
# -----------------------------------------------
st.set_page_config(
    page_title="Fedus Master Price List",
    layout="wide",
    page_icon="🔌"
)

st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# -----------------------------------------------
# Published XLSX link (entire workbook)
# -----------------------------------------------
PUBLISHED_XLSX_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w"
    "/pub?output=xlsx"
)

# -----------------------------------------------
# Load all sheets as DataFrames
# -----------------------------------------------
@st.cache_data(ttl=600)
def load_all_sheets(xlsx_url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(xlsx_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download published XLSX. Status code: {response.status_code}"
        )
    
    return pd.read_excel(
        BytesIO(response.content),
        sheet_name=None,
        engine="openpyxl"
    )

with st.spinner("Syncing all Fedus categories..."):
    try:
        all_sheets = load_all_sheets(PUBLISHED_XLSX_URL)
    except Exception as e:
        st.error(f"Error loading workbook: {e}")
        st.stop()

if not all_sheets:
    st.error("No sheets found in the published workbook.")
    st.stop()

# -----------------------------------------------
# Sidebar navigation
# -----------------------------------------------
sheet_names = list(all_sheets.keys())

st.sidebar.header("Navigation")
selected_sheet = st.sidebar.selectbox("📂 Select Category", sheet_names)

# Checkbox for global search
global_search = st.sidebar.checkbox("🔎 Search across ALL categories")

# -----------------------------------------------
# Search input
# -----------------------------------------------
search_query = st.text_input(
    "Search products",
    placeholder="Search by SKU, title, type, etc."
)

# Helper: search across all columns in a DataFrame
def search_df(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query:
        return df
    return df[
        df.astype(str)
        .apply(lambda row: row.str.contains(query, case=False, na=False))
        .any(axis=1)
    ]

# -----------------------------------------------
# Apply search logic
# -----------------------------------------------
if global_search:
    # Combine all sheets into one DataFrame with a "Category" column
    combined = []
    for name, df in all_sheets.items():
        temp = df.copy()
        temp.insert(0, "Category", name)
        combined.append(temp)
    master_df = pd.concat(combined, ignore_index=True, sort=False)
    display_df = search_df(master_df, search_query)

    st.subheader("🔎 Global Search Results")
    st.write(f"Showing {len(display_df):,} rows matching search.")

else:
    # Only selected category
    df = all_sheets[selected_sheet]
    display_df = search_df(df, search_query)

    st.subheader(f"📂 Category: {selected_sheet}")
    st.write(f"Showing {len(display_df):,} rows.")

# -----------------------------------------------
# Display with optional image/link columns
# -----------------------------------------------
column_config = {}
if "Image" in display_df.columns:
    column_config["Image"] = st.column_config.ImageColumn("Preview")

if "PRODUCT Gallery" in display_df.columns:
    column_config["PRODUCT Gallery"] = st.column_config.LinkColumn(
        "Gallery", display_text="Open Gallery"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config if column_config else None
)

# -----------------------------------------------
# Download filtered results option
# -----------------------------------------------
csv = display_df.to_csv(index=False)
st.download_button(
    "⬇️ Download filtered results (CSV)",
    csv,
    file_name="fedus_price_list.csv",
    mime="text/csv"
)


