import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Fedus Master Price List", layout="wide", page_icon="🔌")

# 2. Styling the Dashboard
st.title("🔌 Fedus Master Price List")
st.markdown("### Search across all 25+ categories | Updated Live")

# 3. Connection Setup (Your specific Sheet ID)
SHEET_ID = "1yccQUPQh8X_JZg8W8BeJQHZVPan6zb1c"
# We download the whole file as XLSX to see all sheets automatically
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# 4. Automatically Fetch All Sheet Names
@st.cache_data(ttl=600)
def get_all_data():
    # This reads all 25+ sheets at once into a dictionary
    return pd.read_excel(URL, sheet_name=None, skiprows=1)

try:
    with st.spinner('Loading your 25+ sheets... please wait...'):
        all_sheets = get_all_data()
    
    sheet_names = list(all_sheets.keys())

    # 5. Sidebar Selection
    st.sidebar.header("Navigation")
    selection = st.sidebar.selectbox("📂 Select a Category", sheet_names)
    
    # Get the data for the selected sheet
    df = all_sheets[selection]

    # 6. Global Search
    search_query = st.text_input(f"🔍 Search in {selection}...", placeholder="Search Title, SKU, or Material")

    if search_query:
        # Searches across the 'Title' column (from your screenshot)
        df = df[df['Title'].astype(str).str.contains(search_query, case=False, na=False)]

    # 7. Beautiful Display with Images
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
    st.info("Check if your Google Sheet is set to 'Anyone with the link can view'.")
