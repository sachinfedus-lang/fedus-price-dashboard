import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Fedus Master Price List", layout="wide", page_icon="🔌")

st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# 2. Connection Setup
SHEET_ID = "1yccQUPQh8X_JZg8W8BeJQHZVPan6zb1c"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=600)
def get_all_data():
    try:
        # Added a User-Agent header to prevent the 401 error
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content), sheet_name=None, skiprows=1)
        else:
            st.error(f"Failed to connect. Status Code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Data error: {e}")
        return None

# 3. Main Logic
all_sheets = get_all_data()

if all_sheets:
    sheet_names = list(all_sheets.keys())
    
    # Sidebar Selection
    st.sidebar.header("Navigation")
    selection = st.sidebar.selectbox("📂 Select Category", sheet_names)
    
    df = all_sheets[selection]

    # Search Bar
    search_query = st.text_input(f"🔍 Search in {selection}...", placeholder="Search Title (e.g. Cat 6)")

    if search_query:
        # Searching the 'Title' column found in your screenshots
        df = df[df['Title'].astype(str).str.contains(search_query, case=False, na=False)]

    # 4. Display
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Image": st.column_config.ImageColumn("Preview"),
            "PRODUCT Gallery": st.column_config.LinkColumn("Gallery", display_text="Open Gallery")
        }
    )
