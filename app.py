import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Fedus Master Price List", layout="wide", page_icon="🔌")

st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# 2. Connection Setup (Using your new Published ID)
# We convert the 'pubhtml' link into a 'pub?output=xlsx' data link
PUBLISHED_ID = "2PACX-1vTYXjBUAeE7-cuVA8tOk5q0rMlFgy0Zy98QB3Twlyth5agxLi9cCRDpG-JumnY_3w"
DATA_URL = f"https://docs.google.com/spreadsheets/d/e/{PUBLISHED_ID}/pub?output=xlsx"

@st.cache_data(ttl=600)
def get_all_data():
    try:
        # Standard headers to ensure a smooth connection
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(DATA_URL, headers=headers)
        if response.status_code == 200:
            # Reads all sheets. skiprows=1 skips your top blue row (Row 1)
            return pd.read_excel(BytesIO(response.content), sheet_name=None, skiprows=1)
        else:
            st.error(f"Google Connection Failed (Status {response.status_code}).")
            return None
    except Exception as e:
        st.error(f"Error downloading data: {e}")
        return None

# 3. Running the Dashboard logic
all_data = get_all_data()

if all_data:
    sheet_names = list(all_data.keys())
    
    # Sidebar Category Navigation
    st.sidebar.header("Navigation")
    selection = st.sidebar.selectbox("📂 Select Category", sheet_names)
    
    # Get the dataframe for the selected sheet
    df = all_data[selection]

    # Search Bar - Filters the 'Title' column as seen in your sheet
    search_query = st.text_input(f"🔍 Search in {selection}...", placeholder="e.g. Cat 6, 100M...")

    if search_query:
        # We ensure Title is treated as a string before searching
        df = df[df['Title'].astype(str).str.contains(search_query, case=False, na=False)]

    # 4. Final Table Display
    # This turns your 'Image' column into pictures and 'PRODUCT Gallery' into buttons
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Image": st.column_config.ImageColumn("Preview"),
            "PRODUCT Gallery": st.column_config.LinkColumn("Gallery", display_text="Open Gallery")
        }
    )
else:
    st.warning("Waiting for data from Google Sheets... please refresh in 30 seconds.")

