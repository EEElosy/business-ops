import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px  # For engineering charts

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nibworks",
    page_icon="🏭",
    layout="wide"
)

# --- CLASS DEFINITION: THE LOGIC ENGINE ---
class InventoryManager:
    def __init__(self):
        # Establish connection using the Secrets we saved
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        
    def load_data(self):
        """Fetches data from Google Sheets with caching."""
        try:
            # ttl=5 ensures we don't hit Google's API limit but get fresh data
            return self.conn.read(worksheet=0, ttl=5)
        except Exception as e:
            st.error(f"⚠️ Data Fetch Error: {e}")
            return pd.DataFrame()

    def update_stock(self, df, item_name, quantity_change, action_type):
        """
        Updates stock based on action.
        action_type: "Sale" (-), "Restock" (+), "Correction" (+/-)
        """
        # Find the specific row index
        # We use .loc to ensure we work on the actual dataframe, not a copy
        idx = df[df["Item"] == item_name].index
        
        if not idx.empty:
            current_stock = df.loc[idx[0], "Stock"]
            
            # Logic Gate for Inventory Physics
            if action_type == "Sale" and current_stock < quantity_change:
                return False, "❌ Error: Insufficient stock for this sale!"
            
            # Apply the Math
            if action_type == "Sale":
                df.loc[idx[0], "Stock"] = current_stock - quantity_change
            elif action_type == "Restock":
                df.loc[idx[0], "Stock"] = current_stock + quantity_change
            
            # Push to Cloud
            self.conn.update(worksheet=0, data=df)
            return True, f"✅ Success: {item_name} stock updated."
        else:
            return False, "❌ Error: Item not found."

    def add_new_item(self, df, item_name, initial_stock):
        """Adds a completely new SKU to the database."""
        if item_name in df["Item"].values:
            return False, "⚠️ Item already exists."
        
        new_row = pd.DataFrame([{"Item": item_name, "Stock": initial_stock}])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        self.conn.update(worksheet=0, data=updated_df)
        return True, f"✅ New SKU '{item_name}' created."

# --- MAIN APP UI ---
def main():
    st.title("🏭 Nibworks")
    
    # Initialize our Logic Engine
    manager = InventoryManager()
    data = manager.load_data()

    # Ensure columns exist (Data Validation)
    if "Item" not in data.columns or "Stock" not in data.columns:
        st.error("DATABASE ERROR: Your Google Sheet must have columns named 'Item' and 'Stock'.")
        st.stop()

    # Create Tabs for neat organization
    tab_ops, tab_data, tab_analytics = st.tabs(["🛠️ Operations", "📦 Inventory", "📊 Analytics"])

    # --- TAB 1: OPERATIONS (The Daily Work) ---
    with tab_ops:
        col1, col2 = st.columns(2)
        
        # Section A: Update Existing Stock
        with col1:
            st.subheader("Update Stock")
            if not data.empty:
                with st.form("update_stock_form"):
                    # Dropdown prevents typo errors
                    selected_item = st.selectbox("Select Item", data["Item"].unique())
                    action = st.radio("Action", ["Sale", "Restock"], horizontal=True)
                    qty = st.number_input("Quantity", min_value=1, value=1)
                    
                    if st.form_submit_button("Update Database"):
                        success, msg = manager.update_stock(data, selected_item, qty, action)
                        if success:
                            st.success(msg)
                            st.rerun() # Refresh immediately
                        else:
                            st.error(msg)
            else:
                st.info("Database is empty. Add items first.")

        # Section B: Create New Item
        with col2:
            st.subheader("New SKU Creation")
            with st.form("new_item_form"):
                new_name = st.text_input("New Item Name")
                new_stock = st.number_input("Initial Stock", min_value=0, value=0)
                
                if st.form_submit_button("Create Item"):
                    if new_name:
                        success, msg = manager.add_new_item(data, new_name, new_stock)
                        if success:
                            st.success(msg)
                            st.rerun()
                    else:
                        st.warning("Please enter a name.")

    # --- TAB 2: INVENTORY (The Database View) ---
    with tab_data:
        st.subheader("Current Stock Levels")
        # Display the raw data as an interactive table
        st.dataframe(data, use_container_width=True)
        
        # Download button for backups
        st.download_button(
            label="📥 Download CSV Backup",
            data=data.to_csv(index=False).encode('utf-8'),
            file_name='inventory_backup.csv',
            mime='text/csv',
        )

    # --- TAB 3: ANALYTICS (The CEO View) ---
    with tab_analytics:
        st.subheader("Stock Visualization")
        if not data.empty:
            # A simple bar chart to visualize low stock
            fig = px.bar(data, x="Item", y="Stock", title="Inventory Levels by SKU", 
                         color="Stock", color_continuous_scale="RdYlGn")
            st.plotly_chart(fig, use_container_width=True)
            
            # Engineering Metrics
            total_stock = data["Stock"].sum()
            sku_count = data["Item"].nunique()
            st.metric("Total Items in Warehouse", f"{total_stock} units")
            st.metric("Active SKUs", sku_count)

if __name__ == "__main__":
    main()


