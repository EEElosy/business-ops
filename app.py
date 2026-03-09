import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import time
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Nibworks ✒️")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
    <style>
    /* Target ONLY primary buttons */
    button[kind="primary"] {
        background-color: #93F59A !important;
        color: #111111 !important; /* Dark text so you can read it */
        border: 1px solid #93F59A !important;
    }
    /* Add a slight darkening effect when you hover over it */
    button[kind="primary"]:hover {
        background-color: #7ce084 !important;
        border: 1px solid #7ce084 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["admin_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("🔐 Enter Admin Password", type="password", on_change=password_entered, key="password")
        return False
    return True

# --- DATABASE ENGINE ---
class DbManager:
    def __init__(self):
        self.conn = st.connection("gsheets", type=GSheetsConnection)

    def _get_sheet_from_memory(self, sheet_name, required_cols):
        state_key = f"db_{sheet_name}"
        if state_key not in st.session_state:
            df = self.conn.read(worksheet=sheet_name, ttl=600)
            st.session_state[state_key] = df
            
        df = st.session_state[state_key]
        for col in required_cols:
            if col not in df.columns: df[col] = ""
        return df

    def _save_sheet_to_memory_and_google(self, sheet_name, df):
        st.session_state[f"db_{sheet_name}"] = df
        self.conn.update(worksheet=sheet_name, data=df)

    def load_inventory(self):
        df = self._get_sheet_from_memory("Inventory", ["Date", "Type", "Brand", "Model", "Color", "Details", "Purchase Price", "Target Price", "Stock", "Supplier", "Currency"])
        df["Stock"] = pd.to_numeric(df["Stock"], errors='coerce').fillna(0)
        df["Purchase Price"] = pd.to_numeric(df["Purchase Price"], errors='coerce').fillna(0.0)
        df["Target Price"] = pd.to_numeric(df["Target Price"], errors='coerce').fillna(0.0)
        if "Currency" not in df.columns: df["Currency"] = "$" 
        return df

    def load_nib_orders(self):
        df = self._get_sheet_from_memory("Nib Orders", ["Date", "Name", "Quantity", "Status", "Price", "Currency"])
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce').fillna(1)
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce').fillna(0.0)
        if "Currency" not in df.columns: df["Currency"] = "$"
        return df

    def add_inventory_item(self, df, item_data):
        updated_df = pd.concat([df, pd.DataFrame([item_data])], ignore_index=True)
        self._save_sheet_to_memory_and_google("Inventory", updated_df)
        return updated_df

    def add_nib_order(self, df, order_data):
        updated_df = pd.concat([df, pd.DataFrame([order_data])], ignore_index=True)
        self._save_sheet_to_memory_and_google("Nib Orders", updated_df)
        return updated_df 

    def update_nib_order(self, df, index, new_status, new_price):
        df.loc[index, "Status"] = new_status
        df.loc[index, "Price"] = float(new_price)
        self._save_sheet_to_memory_and_google("Nib Orders", df)

    def register_sale(self, inventory_df, row_index, final_selling_price, sales_currency, exchange_rate):
        brand = inventory_df.loc[row_index, 'Brand']
        model = inventory_df.loc[row_index, 'Model']
        original_cost = float(inventory_df.loc[row_index, 'Purchase Price']) 
        
        normalized_cost = original_cost * exchange_rate
        item_name = f"{brand} {model}"
        current_stock = inventory_df.loc[row_index, "Stock"]
        
        if current_stock < 1: return False, "❌ Out of Stock!"

        inventory_df.loc[row_index, "Stock"] = current_stock - 1
        self._save_sheet_to_memory_and_google("Inventory", inventory_df)

        sales_data = self._get_sheet_from_memory("Sales", ["Date", "Item Sold", "Quantity", "Selling Price", "Currency", "Cost Price", "Exchange Rate"])

        new_sale = {
            "Date": str(date.today()), "Item Sold": item_name, "Quantity": 1,
            "Selling Price": float(final_selling_price), "Currency": sales_currency,
            "Cost Price": normalized_cost, "Exchange Rate": exchange_rate
        }
        updated_sales = pd.concat([sales_data, pd.DataFrame([new_sale])], ignore_index=True)
        self._save_sheet_to_memory_and_google("Sales", updated_sales)
        return True, f"✅ Sold {item_name} for {final_selling_price} {sales_currency}!"

    def log_expense(self, category, amount, currency, notes):
        exp_data = self._get_sheet_from_memory("Expenses", ["Date", "Category", "Amount", "Currency", "Notes"])
        new_expense = {"Date": str(date.today()), "Category": category, "Amount": float(amount), "Currency": currency, "Notes": notes}
        updated_exp = pd.concat([exp_data, pd.DataFrame([new_expense])], ignore_index=True)
        self._save_sheet_to_memory_and_google("Expenses", updated_exp)
        return True

# --- MAIN APP ---
def main():
    if check_password():
        # --- MAIN HEADER & SMART REFRESH BUTTON ---
        col_title, col_sync = st.columns([4, 1])
        with col_title:
            st.title("Nibworks ERP ✒️")
        with col_sync:
            st.write("") 
            if st.button("🔄 Refresh Data", use_container_width=True):
                # NOTICE: Everything below the 'if' is indented with 4 extra spaces!
                current_time = time.time()
                last_refresh = st.session_state.get("last_refresh", 0)
                
                if current_time - last_refresh < 60:
                    st.toast("⏳ Please wait 60 seconds between manual refreshes to protect the database.", icon="⚠️")
                else:
                    st.session_state["last_refresh"] = current_time
                    
                    # --- SURGICAL WIPE ---
                    for key in list(st.session_state.keys()):
                        if "password" not in key.lower() and key != "last_refresh":
                            del st.session_state[key]
                            
                    st.cache_data.clear() 
                    st.rerun()

        db = DbManager()
        
        try:
            inventory = db.load_inventory()
            nib_orders = db.load_nib_orders()
        except Exception as e:
            st.error(f"⚠️ Database Error: {e}. Check your Sheet Headers!")
            st.stop()

        tab_sell, tab_nib, tab_inv, tab_finance = st.tabs(["💰 Negotiate & Sell", "✒️ Nib Services", "📦 Inventory", "📊 Analytics"])

        # --- TAB 1: OPERATIONS (Omitted for brevity, remains unchanged from previous implementation) ---
        with tab_sell:
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🛒 Transaction")
                search = st.text_input("Find Item", placeholder="Search Brand, Model, Type, Color... (e.g. 'montblanc blue ink')")
                
                # --- Tokenized Multi-Word Search Engine ---
                if search:
                    search_corpus = (
                        inventory["Brand"].astype(str) + " " +
                        inventory["Model"].astype(str) + " " +
                        inventory["Type"].astype(str) + " " +
                        inventory["Color"].astype(str)
                    ).str.lower()
                    
                    search_words = search.lower().split()
                    
                    mask = pd.Series([True] * len(inventory))
                    for word in search_words:
                        mask = mask & search_corpus.str.contains(word, na=False)
                        
                    results = inventory[mask]
                else:
                    results = inventory

                if not results.empty:
                    options = results.index.tolist()
                    
                    # --- Dynamic Label Formatter ---
                    def labeler(i):
                        row = results.loc[i]
                        raw_color = str(row['Color']).strip()
                        if raw_color.lower() != 'nan' and raw_color != '':
                            color_display = f" ({raw_color})"
                        else:
                            color_display = ""
                        return f"{row['Type']} | {row['Brand']} {row['Model']}{color_display}"
                    
                    selected_idx = st.selectbox("Select Item", options, format_func=labeler)
                    
                    # --- NEGOTIATION ENGINE ---
                    row = results.loc[selected_idx]
                    cost = float(row["Purchase Price"])
                    target = float(row["Target Price"])
                    item_currency = row["Currency"] if "Currency" in row else "$"

                    st.info(f"📊 **Original Cost:** {cost} {item_currency} | **Target:** {target} {item_currency}")
                    
                    # 1. Price & Currency Input (Now increments by 100)
                    col_p, col_c = st.columns([2, 1])
                    final_price = col_p.number_input("Final Agreed Price", value=target, step=100.0)
                    sales_curr = col_c.selectbox("Sales Currency", ["₺", "$", "€", "£"], index=["₺", "$", "€", "£"].index(item_currency) if item_currency in ["₺", "$", "€", "£"] else 0)
                    
                    # 2. Exchange Rate Logic
                    exchange_rate = 1.0
                    if sales_curr != item_currency:
                        st.write(f"⚠️ **Conversion Needed:** You are selling in **{sales_curr}**, but bought in **{item_currency}**.")
                        exchange_rate = st.number_input(f"Enter Exchange Rate (1 {item_currency} = ? {sales_curr})", value=1.0, format="%.4f")
                        
                        new_cost = cost * exchange_rate
                        st.caption(f"ℹ️ Normalized Cost: {cost} {item_currency} × {exchange_rate} = **{new_cost:.2f} {sales_curr}**")
                        cost = new_cost 

                    # Margin Warning (Only triggers if selling below cost)
                    if final_price < cost:
                        st.warning(f"⚠️ Loss Alert: Selling {cost - final_price:.2f} {sales_curr} below cost!")

                    # Confirm Button 
                    if st.button("✅ Confirm Sale", type="primary"):
                        success, msg = db.register_sale(inventory, selected_idx, final_price, sales_curr, exchange_rate)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with c2:
                st.subheader("💸 Log Expense")
                with st.form("expense_form"):
                    cat = st.selectbox("Category", ["Shipment", "Taxi", "Food & Beverages", "Salary", "Debt", "Inventory Purchase", "Other"])
                    e_col1, e_col2 = st.columns([2, 1])
                    amt = e_col1.number_input("Amount", min_value=0.0, step=50.0)
                    curr = e_col2.selectbox("Currency", ["₺", "$", "€", "£"])
                    note = st.text_input("Note")
                    
                    if st.form_submit_button("Save Expense"):
                        db.log_expense(cat, amt, curr, note)
                        st.success("Expense Saved!")
                        
        # --- TAB 2: NIB CUSTOMIZATION SERVICES ---
        with tab_nib:
            col_queue, col_new = st.columns([2, 1])
            
            with col_new:
                st.subheader("➕ New Nib Order")
                
                # 1. We create an "empty placeholder" at the TOP of the section
                # so the error message appears above the form, not below it.
                msg_box = st.empty() 
                
                with st.form("new_nib", clear_on_submit=True):
                    n_date = st.date_input("Order Date", value=date.today())
                    n_name = st.text_input("Customer/Order Name")
                    n_qty = st.number_input("Quantity", min_value=1, step=1)
                    n_price = st.number_input("Quoted Price", value=0.0, step=50.0)
                    n_curr = st.selectbox("Currency", ["₺", "$", "€", "£"])
                    
                    if st.form_submit_button("Create Order"):
                        if n_name:
                            nib_orders = db.add_nib_order(nib_orders, {
                                "Date": str(n_date), "Name": n_name, "Quantity": n_qty,
                                "Status": "In Progress", "Price": n_price, "Currency": n_curr
                            })
                            # Floating popup + Top message
                            st.toast("Order successfully created!", icon="✅")
                            msg_box.success("✅ Order Added!")
                        else:
                            # Floating error popup + Top error message
                            st.toast("Missing Customer Name!", icon="🚨")
                            msg_box.error("⚠️ Customer Name is required.")
            with col_queue:
                st.subheader("📋 Active Work Queue")
                active_mask = nib_orders["Status"] == "In Progress"
                active_orders = nib_orders[active_mask]
                
                if active_orders.empty:
                    st.success("All caught up! No active orders.")
                else:
                    for idx, row in active_orders.iterrows():
                        order_date = datetime.strptime(str(row["Date"]), "%Y-%m-%d").date()
                        days_waiting = (date.today() - order_date).days
                        
                        with st.container():
                            st.markdown(f"**{row['Name']}** | 📦 Qty: {row['Quantity']}")
                            st.markdown(f"🔴 *In Progress* — Waiting: **{days_waiting} days**")
                            
                            # The Fix: Use vertical_alignment="bottom" and specific column widths
                            # This automatically aligns the bottom of the input box, text, and button.
                            c_price, c_sym, c_btn = st.columns([2, 0.5, 2], vertical_alignment="bottom")
                            
                            with c_price:
                                new_p = st.number_input("Final Price", value=float(row["Price"]), step=50.0, key=f"p_{idx}")
                            
                            with c_sym:
                                # Removed the awful st.write("##") spacers
                                st.markdown(f"**{row['Currency']}**")
                            
                            with c_btn:
                                if st.button("✅ Mark Completed", key=f"btn_{idx}", use_container_width=True):
                                    db.update_nib_order(nib_orders, idx, "Completed", new_p)
                                    st.toast(f"Completed {row['Name']}!", icon="🎉")
                                    st.rerun()
                                    
                            st.divider()

            st.subheader("✅ Completed Orders")
            completed_orders = nib_orders[nib_orders["Status"] == "Completed"]
            st.dataframe(completed_orders, use_container_width=True)

        # --- TAB 3: INVENTORY (Omitted for brevity, remains unchanged) ---
        with tab_inv:
            with st.expander("➕ Add New Inventory"):
                with st.form("add_inv", clear_on_submit=True):
                    # Row 1: Type is now placed before Brand
                    c_date, c_type, c_brand, c_model = st.columns(4)
                    d = c_date.date_input("Date", value=date.today())
                    item_type = c_type.selectbox("Type", ["Fountain Pen", "Ink", "Nib", "Notebook", "Accessory", "Other"])
                    b = c_brand.text_input("Brand")
                    m = c_model.text_input("Model")
                    
                    c_col, c_det, c_sup = st.columns(3)
                    color = c_col.text_input("Color")
                    det = c_det.text_input("Details")
                    sup = c_sup.text_input("Supplier")
                    
                    c_cost, c_target, c_stock, c_cur = st.columns(4)
                    cost_p = c_cost.number_input("Purchase Price (Cost)", value=0.0)
                    targ_p = c_target.number_input("Target Sale Price", value=0.0)
                    stk = c_stock.number_input("Stock", value=1, step=1)
                    cur = c_cur.selectbox("Currency", ["₺", "$", "€", "£"])
                    
                    if st.form_submit_button("Save Item"):
                        new_item = {
                            "Date":str(d), "Type": item_type, "Brand":b, "Model":m, "Color":color, "Details":det,
                            "Purchase Price":cost_p, "Target Price":targ_p, 
                            "Stock":stk, "Supplier":sup, "Currency":cur
                        }
                        db.add_inventory_item(inventory, new_item)
                        st.success(f"Added {b} {m} ({item_type})!")
                        st.rerun()
            st.subheader("Current Stock")
            st.dataframe(inventory, use_container_width=True)

        # --- TAB 4: REAL PROFIT & ANALYTICS ---
        with tab_finance:
            st.subheader("Profitability & Operational Volume")
            try:
                sales_df = db._get_sheet_from_memory("Sales", ["Selling Price", "Cost Price", "Currency", "Date", "Item Sold"])
                expense_df = db._get_sheet_from_memory("Expenses", ["Amount", "Currency"])
                
                sales_df["Selling Price"] = pd.to_numeric(sales_df["Selling Price"], errors='coerce').fillna(0)
                sales_df["Cost Price"] = pd.to_numeric(sales_df["Cost Price"], errors='coerce').fillna(0)
                expense_df["Amount"] = pd.to_numeric(expense_df["Amount"], errors='coerce').fillna(0)

                # NIB ORDER VOLUME ANALYTICS
                st.write("### ✒️ Nib Service Volume")
                if not nib_orders.empty:
                    nib_orders["DateObj"] = pd.to_datetime(nib_orders["Date"], errors='coerce')
                    today = pd.to_datetime(date.today())
                    
                    # Filtering operations via timedelta
                    orders_7d = nib_orders[nib_orders["DateObj"] >= (today - timedelta(days=7))]
                    orders_30d = nib_orders[nib_orders["DateObj"] >= (today - timedelta(days=30))]
                    
                    v1, v2, v3 = st.columns(3)
                    v1.metric("Orders (Last 7 Days)", len(orders_7d))
                    v2.metric("Orders (Last 30 Days)", len(orders_30d))
                    v3.metric("Pending Queue", len(nib_orders[nib_orders["Status"] == "In Progress"]))
                
                st.divider()

                # --- NEW: PHYSICAL SALES REPORT ---
                st.write("### 📦 Products Sold")
                if not sales_df.empty:
                    sales_df["DateObj"] = pd.to_datetime(sales_df["Date"], errors='coerce')
                    today = pd.to_datetime(date.today())
                    
                    timeframe = st.radio("Select Timeframe", ["Last 7 Days", "Last 30 Days", "All Time"], horizontal=True, label_visibility="collapsed")
                    
                    if timeframe == "Last 7 Days":
                        filtered_sales = sales_df[sales_df["DateObj"] >= (today - timedelta(days=7))].copy()
                    elif timeframe == "Last 30 Days":
                        filtered_sales = sales_df[sales_df["DateObj"] >= (today - timedelta(days=30))].copy()
                    else:
                        filtered_sales = sales_df.copy()
                    
                    if not filtered_sales.empty:
                        filtered_sales["Gross Margin"] = filtered_sales["Selling Price"] - filtered_sales["Cost Price"]
                        display_sales = filtered_sales[["Date", "Item Sold", "Selling Price", "Gross Margin", "Currency"]]
                        
                        st.dataframe(display_sales, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No physical items sold in the {timeframe.lower()}.")
                else:
                    st.info("No sales data available yet.")

                st.divider()

                # FINANCIAL AGGREGATION
                st.write("### 💰 Consolidated Profit by Currency")
                completed_nibs = nib_orders[nib_orders["Status"] == "Completed"]
                
                all_currencies = set(sales_df["Currency"].unique()) | set(expense_df["Currency"].unique()) | set(completed_nibs["Currency"].unique())
                all_currencies.discard("") # Remove empty strings if present
                
                if not all_currencies:
                    st.info("No financial data yet.")
                else:
                    cols = st.columns(len(all_currencies))
                    for i, currency in enumerate(all_currencies):
                        # Revenue streams
                        product_rev = sales_df[sales_df["Currency"] == currency]["Selling Price"].sum()
                        service_rev = completed_nibs[completed_nibs["Currency"] == currency]["Price"].sum()
                        total_rev = product_rev + service_rev
                        
                        # Costs
                        cogs = sales_df[sales_df["Currency"] == currency]["Cost Price"].sum()
                        exp = expense_df[expense_df["Currency"] == currency]["Amount"].sum()
                        
                        net_profit = total_rev - cogs - exp
                        
                        with cols[i]:
                            st.metric(
                                f"Net Profit ({currency})", f"{net_profit:,.2f}", 
                                delta=f"Rev: {total_rev} (Prod: {product_rev}, Serv: {service_rev}) | Cost/Exp: {cogs + exp}"
                            )

            except Exception as e:
                st.info(f"Financials waiting for data... ({e})")

if __name__ == "__main__":
    main()


















