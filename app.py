import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(layout="wide", page_title="Nibworks ERP")

# --- LOGIC ENGINE ---
class InventoryManager:
    def __init__(self):
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        
    def load_data(self):
        # Fetch data with 5-second cache
        df = self.conn.read(worksheet=0, ttl=5)
        
        # 1. Define Standard Columns (Now includes Supplier)
        required_cols = ["Date", "Brand", "Model", "Color", "Details", "Stock", "Price", "Supplier"]
        
        # 2. Fix Missing Columns (Engineering Safety)
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        # 3. Type Conversion (Math Safety)
        df["Stock"] = pd.to_numeric(df["Stock"], errors='coerce').fillna(0)
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce').fillna(0.0)
        df["Date"] = df["Date"].astype(str)
        
        return df

    def add_item(self, df, item_data):
        new_row = pd.DataFrame([item_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        self.conn.update(worksheet=0, data=updated_df)
        return True

    def update_stock(self, df, row_index, change):
        # We use the Row Index to be 100% sure we update the right item
        current_stock = df.loc[row_index, "Stock"]
        new_stock = max(0, current_stock + change)
        df.loc[row_index, "Stock"] = new_stock
        self.conn.update(worksheet=0, data=df)
        return True

# --- HELPER: SEARCH FILTER ---
def filter_dataframe(df, search_term):
    if not search_term:
        return df
    term = search_term.lower()
    
    # Search across all relevant text columns (Including Supplier)
    mask = (
        df["Brand"].astype(str).str.lower().str.contains(term) |
        df["Model"].astype(str).str.lower().str.contains(term) |
        df["Color"].astype(str).str.lower().str.contains(term) |
        df["Supplier"].astype(str).str.lower().str.contains(term) |
        df["Details"].astype(str).str.lower().str.contains(term) |
        df["Date"].astype(str).str.contains(term)
    )
    return df[mask]

# --- MAIN APP ---
def main():
    st.title("🏭 Nibworks")
    
    manager = InventoryManager()
    data = manager.load_data()

    # Create Tabs
    tab_search, tab_add, tab_audit = st.tabs(["🔍 Search & Sell", "➕ Add New Item", "📋 Full List"])

    # --- TAB 1: SEARCH & SELL ---
    with tab_search:
        st.subheader("Find Inventory")
        
        # Search Bar
        search_query = st.text_input("Type to search (Brand, Supplier, Date...)", placeholder="e.g. Nike, FootLocker, Red...")
        
        # Filter Data
        filtered_df = filter_dataframe(data, search_query)
        
        # Display as a clean table
        st.dataframe(
            filtered_df, 
            use_container_width=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Stock": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=50),
            }
        )
        
        st.divider()
        
        # SELL SECTION
        if not filtered_df.empty:
            st.write("### ⚡ Quick Actions")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # We create a "Readable Name" for the dropdown
                options = filtered_df.index.tolist()
                
                def label_maker(idx):
                    row = filtered_df.loc[idx]
                    return f"{row['Brand']} {row['Model']} ({row['Color']}) - Stock: {row['Stock']}"

                selected_index = st.selectbox("Select Item to Update:", options, format_func=label_maker)

            with col2:
                st.write("##") # Spacer
                if st.button("➖ Sell 1 Unit", type="primary"):
                    manager.update_stock(data, selected_index, -1)
                    st.success("Sold! Stock updated.")
                    st.rerun()

    # --- TAB 2: ADD NEW ITEM ---
    with tab_add:
        st.subheader("Register Stock")
        
        with st.form("new_entry"):
            # row 1: Identification
            c1, c2, c3 = st.columns(3)
            date_picked = c1.date_input("Date Added", value=date.today())
            brand = c2.text_input("Brand", placeholder="e.g. Nike")
            supplier = c3.text_input("Supplier", placeholder="e.g. Factory A")
            
            # row 2: Specifics
            c4, c5 = st.columns(2)
            model = c4.text_input("Model", placeholder="e.g. Air Force 1")
            color = c5.text_input("Color", placeholder="e.g. White")
            
            # row 3: Meta
            details = st.text_area("Details / Hashtags", placeholder="e.g. #summer #sale #damaged_box")
            
            # row 4: Numbers
            c6, c7 = st.columns(2)
            stock = c6.number_input("Quantity", min_value=0, value=1)
            price = c7.number_input("Purchase Price", min_value=0.0, step=0.5)
            
            if st.form_submit_button("💾 Save to Database"):
                if brand and model:
                    new_item = {
                        "Date": str(date_picked),
                        "Brand": brand,
                        "Model": model,
                        "Color": color,
                        "Details": details,
                        "Stock": int(stock),
                        "Price": float(price),
                        "Supplier": supplier
                    }
                    manager.add_item(data, new_item)
                    st.success(f"✅ Added {brand} {model} to inventory!")
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter at least a Brand and Model.")

    # --- TAB 3: AUDIT ---
    with tab_audit:
        st.write(f"Total Items in Database: **{len(data)}**")
        st.dataframe(data, use_container_width=True)

if __name__ == "__main__":
    main()

