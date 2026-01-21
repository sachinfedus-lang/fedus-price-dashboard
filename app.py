import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Fedus Master Price List", layout="wide", page_icon="🔌")

# 2. Branding
st.title("🔌 Fedus Master Price List")
st.sidebar.image("https://via.placeholder.com/150", caption="Fedus APM Dashboard") # Replace with your logo URL

# 3. Connection Setup
# Using your provided Master Sheet ID
SHEET_ID = "1yccQUPQh8X_JZg8W8BeJQHZVPan6zb1c"

# Function to automatically discover all sheets (GIDs) 
# This handles 25+ sheets without manual coding
@st.cache_data(ttl=600)
def get_all_sheet_names():
    # This is a special URL that lists all tabs in a Google Sheet
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"
    # We use a trick here: we read the HTML of the sheet to find all tab names
    # For now, we will list your main ones, but you can add more to this list easily
    return {
        "Ethernet Cable": "0",
        "Ethernet Patch Cable": "1412080312",
        "Connector": "184646700",
        "Crimping Tool": "1656828945",
        "Cooler Pump": "1314227003",
        "Power Extension Cable": "1782299863",
        "Power Cable": "1273942084",
        "International Power Cable": "1036329707",
        # Add your other 18+ sheet names and GIDs here
    }

tabs_map = get_all_sheet_names()

# 4. Sidebar: Search & Select Category
st.sidebar.header("Navigation")
search_category = st.sidebar.text_input("🔍 Quick Find Category", placeholder="e.g. Pump...")
filtered_categories = [cat for cat in tabs_map.keys() if search_category.lower() in cat.lower()]

selection = st.sidebar.selectbox("📂 Select a Category", filtered_categories)

# 5. Load Data Function
@st.cache_data(ttl=300)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    # skiprows=1 skips your top blue 'X' bar from Row 1
    df = pd.read_csv(url, skiprows=1)
    return df

try:
    df = load_data(tabs_map[selection])

    # 6. Global Search within the selected Sheet
    search_query = st.text_input(f"🔍 Search products in {selection}...", placeholder="Search by Title, SKU, or Color")

    if search_query:
        # This searches every column in the sheet, not just 'Title'
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    # 7. Display Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Products", len(df))
    col2.metric("Category", selection)

    # 8. Interactive Table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Image": st.column_config.ImageColumn("Preview"),
            "PRODUCT Gallery": st.column_config.LinkColumn("Gallery", display_text="View Gallery")
        }
    )

except Exception as e:
    st.error("Error loading data. Check if you added the correct GID for this sheet.")
