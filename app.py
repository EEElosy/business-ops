import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🏭 Engineering Ops Console")

# 1. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Fetch Data
# This reads the first sheet (Worksheet 0)
try:
    data = conn.read(worksheet=0, ttl=5)
    st.success("✅ Connected to Google Sheets!")
    st.write("### 📦 Live Inventory")
    st.dataframe(data)
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")

# 3. Add Item Form
with st.expander("Add New Item"):
    with st.form("new_item"):
        item_name = st.text_input("Item Name")
        stock = st.number_input("Stock", step=1)
        
        if st.form_submit_button("Save to Cloud"):
            # Create a new row
            new_row = pd.DataFrame([{"Item": item_name, "Stock": stock}])
            
            # Append to Google Sheet
            updated_df = pd.concat([data, new_row], ignore_index=True)
            conn.update(worksheet=0, data=updated_df)
            
            st.success("Saved!")
            st.rerun()
