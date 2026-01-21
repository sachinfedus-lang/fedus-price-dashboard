import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Fedus Master Price List", layout="wide", page_icon="🔌")

# 2. Styling
st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# 3. Connection Setup (Your specific Sheet ID)
SHEET_ID = "1yccQUPQh8X_JZg8W8BeJQHZVPan6zb1c"
# This is the "Universal" link that bypasses the 401 error for public sheets
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=600)
def get_all_data():
    # We use 'requests' to download the file directly
    response = requests.get(URL)
    # Check if the download was successful
    if response.status_code == 200:
        return pd.read_excel(BytesIO(response.content), sheet_name=None, skiprows=1)
    else:
        st.error(f"Failed to download. Status Code: {response.status_code}")
        return None

try:
    with st.spinner('Syncing all 25+ Fedus categories...'):
        all_sheets = get_all_data()
    
    if all_sheets:
        sheet_names = list(all_sheets.keys())

        # 4. Sidebar Selection
        st.sidebar.header("Navigation")
        selection = st.sidebar.selectbox("📂 Select Category", sheet_names)
        
        # Get data for the selected sheet
        df = all_sheets[selection]

        # 5. Global Search
        search_query = st.text_input(f"🔍 Search in {selection}...", placeholder="Search Title (e.g. Cat 6)")

        if search_query:
            # Filters the Title column based on your sheet headers
            df = df[df['Title'].astype(str).str.contains(search_query, case=False, na=False)]

        # 6. Final Dashboard Display
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Image": st.column_config.ImageColumn("Preview"),
                "PRODUCT Gallery": st.column_config.LinkColumn("Gallery", display_text="Open Gallery")
            }
        )

except Exception as e:
    st.error(f"Error: {e}")
