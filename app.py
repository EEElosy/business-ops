import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import time
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Nibworks ✒️")

# ── DESIGN SYSTEM ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

.stApp { background-color: #F7F6F2 !important; }
.block-container { padding-top: 2rem !important; max-width: 1200px !important; }

h1 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 300 !important;
    font-size: 26px !important;
    letter-spacing: -.4px !important;
    color: #1A1A1A !important;
}
h2, h3 {
    font-weight: 400 !important;
    font-size: 13px !important;
    color: #888 !important;
    text-transform: uppercase !important;
    letter-spacing: .07em !important;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: #EDEDEA !important;
    border-radius: 10px !important;
    padding: 3px !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 18px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    color: #888 !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* PRIMARY BUTTON */
button[kind="primary"] {
    background-color: #C8F7CC !important;
    color: #1A5C22 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: background .15s ease !important;
}
button[kind="primary"]:hover { background-color: #A8EEB0 !important; }

/* SECONDARY BUTTON */
button[kind="secondary"] {
    background-color: transparent !important;
    color: #888 !important;
    border: 0.5px solid #DDDDD8 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}

/* INPUTS */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border: 0.5px solid #DDDDD8 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    color: #1A1A1A !important;
}
[data-baseweb="input"]:focus-within,
[data-baseweb="select"]:focus-within {
    border-color: #93F59A !important;
    box-shadow: 0 0 0 3px rgba(147,245,154,0.2) !important;
}

/* FORM */
[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 0.5px solid #EDEDEA !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
}

/* METRICS */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 0.5px solid #EDEDEA !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
    color: #999 !important;
    font-weight: 400 !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 400 !important;
    color: #1A1A1A !important;
    font-family: 'DM Mono', monospace !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 0.5px solid #EDEDEA !important;
}

/* ALERTS */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 13px !important; }

/* DIVIDER */
hr { border-color: #EDEDEA !important; margin: 1.5rem 0 !important; }

/* TOAST */
[data-testid="stToast"] { border-radius: 10px !important; font-size: 13px !important; }

/* NIB TAB CUSTOM STYLES */
.nib-section-label {
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #999;
    margin-bottom: 10px;
}
.nib-order-card {
    background: #FFFFFF;
    border: 0.5px solid #E8E6E0;
    border-radius: 10px;
    padding: .9rem 1rem;
    margin-bottom: 8px;
}
.nib-order-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.nib-order-name { font-size: 14px; font-weight: 500; color: #1A1A1A; }
.nib-order-meta { font-size: 11px; color: #AAA; margin-top: 2px; }
.nib-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 20px;
    white-space: nowrap;
}
.nib-badge-warn { background: #FAEEDA; color: #854F0B; }
.nib-badge-ok   { background: #EAF3DE; color: #3B6D11; }
.nib-badge-prog { background: #EEEDFE; color: #3C3489; }

.comp-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 0.5px solid #F0EFEB;
    font-size: 13px;
}
.comp-row:last-child { border-bottom: none; }
.comp-name { color: #1A1A1A; }
.comp-date { font-size: 11px; color: #BBB; }
.comp-price { font-family: 'DM Mono', monospace; font-weight: 500; color: #1A1A1A; }
</style>
""", unsafe_allow_html=True)



# --- AUTHENTICATION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    def password_entered():
        if st.session_state.get("password", "") == st.secrets["passwords"]["admin_password"]:
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
        # 1. FORCE LIVE READ: 0-second cache ensures we never overwrite someone else's recent entry
        st.cache_data.clear()
        live_df = self.conn.read(worksheet="Inventory", ttl=0)
        
        # 2. Append to the LIVE data
        updated_df = pd.concat([live_df, pd.DataFrame([item_data])], ignore_index=True)
        self.update_sheet("Inventory", updated_df)
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
        
        # 1. READ LIVE INVENTORY FIRST
        st.cache_data.clear()
        live_inv = self.conn.read(worksheet="Inventory", ttl=0)
        
        # 2. DO THE MATH USING GOOGLE'S ACTUAL NUMBERS, NOT THE STALE MEMORY
        actual_live_stock = live_inv.loc[row_index, "Stock"]
        
        if actual_live_stock < 1: 
            return False, "❌ Out of Stock!"

        # 3. DEDUCT AND SAVE
        live_inv.loc[row_index, "Stock"] = actual_live_stock - 1
        self.conn.update(worksheet="Inventory", data=live_inv)

        # 4. LOG THE SALE
        live_sales = self.conn.read(worksheet="Sales", ttl=0)
        new_sale = {
            "Date": str(date.today()), "Item Sold": item_name, "Quantity": 1,
            "Selling Price": float(final_selling_price), "Currency": sales_currency,
            "Cost Price": normalized_cost, "Exchange Rate": exchange_rate
        }
        updated_sales = pd.concat([live_sales, pd.DataFrame([new_sale])], ignore_index=True)
        self.conn.update(worksheet="Sales", data=updated_sales)
        
        # 5. NUKE THE CACHE SO THE APP KNOWS TO DOWNLOAD THE NEWEST SHEET
        st.cache_data.clear()
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
                            for key in list(st.session_state.keys()):
                                if "password" not in key.lower() and key != "last_refresh":
                                    del st.session_state[key]
                            st.cache_data.clear()
                            import time
                            time.sleep(1.5) 
                            st.rerun()
                        else:
                            st.error(msg)

            with c2:
                st.subheader("💸 Log Expense")
                with st.form("expense_form"):
                    cat = st.selectbox("Category", ["Shipment", "Bank/Card", "Food & Beverages", "Salary", "Taxi", "Debt", "Inventory Purchase", "Other"])
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
                    item_type = c_type.selectbox("Type", ["Pen", "Ink", "Nib", "Notebook", "Accessory", "Other"])
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
            # 1. Made the main title smaller (subheader instead of header)
            st.subheader("📊 Financial Analytics") 
            try:
                # Load Data
                sales_df = db._get_sheet_from_memory("Sales", ["Selling Price", "Cost Price", "Currency", "Date", "Item Sold"])
                expense_df = db._get_sheet_from_memory("Expenses", ["Amount", "Category", "Currency", "Date"])
                inv_df = db._get_sheet_from_memory("Inventory", ["Type", "Brand", "Model"]) # Added to look up item types!

                # 2. AGGRESSIVE DATA CLEANING
                sales_df["DateObj"] = pd.to_datetime(sales_df["Date"], errors='coerce', dayfirst=True, format='mixed')
                expense_df["DateObj"] = pd.to_datetime(expense_df["Date"], errors='coerce', dayfirst=True, format='mixed')
                
                sales_df["Selling Price"] = pd.to_numeric(sales_df["Selling Price"].astype(str).str.replace(r'[^\d\.,]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
                sales_df["Cost Price"] = pd.to_numeric(sales_df["Cost Price"].astype(str).str.replace(r'[^\d\.,]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
                expense_df["Amount"] = pd.to_numeric(expense_df["Amount"].astype(str).str.replace(r'[^\d\.,]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)

                # Prep Nib Orders for bulletproof math
                if not nib_orders.empty:
                    nib_orders["DateObj"] = pd.to_datetime(nib_orders["Date"], errors='coerce', dayfirst=True, format='mixed')
                    nib_orders["Price"] = pd.to_numeric(nib_orders["Price"].astype(str).str.replace(r'[^\d\.,]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
                    
                    # THIS IS WHAT SAVES YOUR 3750 ROW: Strips hidden spaces and forces correct capitalization
                    nib_orders["Status"] = nib_orders["Status"].astype(str).str.strip().str.title()
                else:
                    nib_orders["DateObj"] = pd.Series(dtype='datetime64[ns]')
                    nib_orders["Price"] = pd.Series(dtype='float64')
                    nib_orders["Status"] = pd.Series(dtype='object')
                # Prep Nib Orders for bulletproof math
                if not nib_orders.empty:
                    nib_orders["DateObj"] = pd.to_datetime(nib_orders["Date"], errors='coerce')
                    # Strip symbols and convert European commas
                    nib_orders["Price"] = pd.to_numeric(nib_orders["Price"].astype(str).str.replace(r'[^\d\.,]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
                    
                    # Fix spelling/spacing errors in the Status column (e.g. " completed " becomes "Completed")
                    nib_orders["Status"] = nib_orders["Status"].astype(str).str.strip().str.title()
                else:
                    nib_orders["DateObj"] = pd.Series(dtype='datetime64[ns]')
                    nib_orders["Price"] = pd.Series(dtype='float64')
                    nib_orders["Status"] = pd.Series(dtype='object')

                # Prep Nib Orders
                if not nib_orders.empty:
                    nib_orders["DateObj"] = pd.to_datetime(nib_orders["Date"], errors='coerce')
                    nib_orders["Price"] = pd.to_numeric(nib_orders["Price"], errors='coerce').fillna(0)
                else:
                    nib_orders["DateObj"] = pd.Series(dtype='datetime64[ns]')
                    nib_orders["Price"] = pd.Series(dtype='float64')
                    nib_orders["Status"] = pd.Series(dtype='object')

                # Setup Time Filters
                now = pd.Timestamp.now()
                seven_days_ago = now - pd.Timedelta(days=7)
                
                month_sales = sales_df[sales_df["DateObj"].dt.month == now.month]
                week_sales = sales_df[sales_df["DateObj"] >= seven_days_ago]
                
                month_exp = expense_df[expense_df["DateObj"].dt.month == now.month]
                week_exp = expense_df[expense_df["DateObj"] >= seven_days_ago]

                completed_nibs = nib_orders[nib_orders["Status"] == "Completed"] if not nib_orders.empty else pd.DataFrame(columns=["DateObj", "Price"])
                month_nibs = completed_nibs[completed_nibs["DateObj"].dt.month == now.month]
                week_nibs = completed_nibs[completed_nibs["DateObj"] >= seven_days_ago]

                # --- SECTION 1: NET PROFIT ---
                st.write("#### 💰 Net Profit")
                
                def calc_profit(s_df, e_df, n_df):
                    rev = s_df["Selling Price"].sum() + n_df["Price"].sum()
                    costs = s_df["Cost Price"].sum() + e_df["Amount"].sum()
                    return rev - costs

                p1, p2, p3 = st.columns(3)
                p1.metric("All-Time Profit", f"{calc_profit(sales_df, expense_df, completed_nibs):,.2f}")
                p2.metric("This Month Profit", f"{calc_profit(month_sales, month_exp, month_nibs):,.2f}")
                p3.metric("Last 7 Days Profit", f"{calc_profit(week_sales, week_exp, week_nibs):,.2f}")

                st.divider()

                # --- SECTION 2: NIB SERVICE VOLUME ---
                st.write("#### ✒️ Nib Service Volume")
                if not nib_orders.empty:
                    orders_7d = nib_orders[nib_orders["DateObj"] >= seven_days_ago]
                    orders_30d = nib_orders[nib_orders["DateObj"] >= (now - pd.Timedelta(days=30))]
                    
                    v1, v2, v3 = st.columns(3)
                    v1.metric("Orders (Last 7 Days)", len(orders_7d))
                    v2.metric("Orders (Last 30 Days)", len(orders_30d))
                    v3.metric("Pending Queue", len(nib_orders[nib_orders["Status"] == "In Progress"]))
                else:
                    st.info("No Nib Orders yet.")

                st.divider()

                # --- SECTION 3: SIDE-BY-SIDE PIE CHARTS ---
                current_month_name = now.strftime("%B")
                st.write(f"#### 🍩 {current_month_name} Breakdown")
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    st.write("**Expenses by Category**")
                    if not month_exp.empty:
                        exp_pie_data = month_exp.groupby("Category")["Amount"].sum().reset_index()
                        fig_exp = px.pie(
                            exp_pie_data, values='Amount', names='Category', hole=0.4, 
                            color_discrete_sequence=px.colors.sequential.RdBu
                        )
                        fig_exp.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_exp, use_container_width=True)
                    else:
                        st.info("No expenses logged this month.")

                with chart_col2:
                    st.write("**Revenue by Category**")
                    
                    if not month_sales.empty or not month_nibs.empty:
                        # 1. AGGRESSIVE CLEANING: Lowercase and strip spaces for a flawless match
                        inv_df["Item Key"] = (inv_df["Brand"].fillna("").astype(str) + " " + inv_df["Model"].fillna("").astype(str)).str.strip().str.lower()
                        type_mapping = dict(zip(inv_df["Item Key"], inv_df["Type"].fillna("").astype(str).str.lower()))
                        
                        month_sales_chart = month_sales.copy()
                        if not month_sales_chart.empty:
                            month_sales_chart["Clean Sold"] = month_sales_chart["Item Sold"].astype(str).str.strip().str.lower()
                            
                            # Map using the cleaned names
                            month_sales_chart["Raw Category"] = month_sales_chart["Clean Sold"].map(type_mapping).fillna("")
                            
                            # 2. THE RUTHLESS FILTER: Checks both columns for the exact letters i-n-k
                            month_sales_chart["Category"] = month_sales_chart.apply(
                                lambda row: "Ink" if "ink" in str(row["Raw Category"]) or "ink" in str(row["Clean Sold"]) else "Pen",
                                axis=1
                            )
                            
                            rev_pie_data = month_sales_chart.groupby("Category")["Selling Price"].sum().reset_index()
                            rev_pie_data.rename(columns={"Selling Price": "Amount"}, inplace=True)
                        else:
                            rev_pie_data = pd.DataFrame(columns=["Category", "Amount"])

                        # Inject Nib Services
                        nib_rev = month_nibs["Price"].sum()
                        if nib_rev > 0:
                            nib_row = pd.DataFrame([{"Category": "Nib Services", "Amount": nib_rev}])
                            rev_pie_data = pd.concat([rev_pie_data, nib_row], ignore_index=True)

                        if not rev_pie_data.empty:
                            fig_rev = px.pie(
                                rev_pie_data, values='Amount', names='Category', hole=0.4, 
                                color_discrete_sequence=px.colors.sequential.Tealgrn
                            )
                            fig_rev.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_rev, use_container_width=True)
                        else:
                            st.info("No revenue data to chart.")
                    else:
                        st.info("No revenue logged this month.")

                st.divider()

                # Aggregate totals for the separate numerical blocks
                total_rev = sales_df['Selling Price'].sum() + completed_nibs['Price'].sum()
                month_rev = month_sales['Selling Price'].sum() + month_nibs['Price'].sum()
                week_rev = week_sales['Selling Price'].sum() + week_nibs['Price'].sum()

                # --- SECTION 4: REVENUE NUMERICALS ---
                st.write("#### 📈 Revenue Details")
                r1, r2, r3 = st.columns(3)
                r1.metric("All-Time Revenue", f"{total_rev:,.2f}")
                r2.metric("This Month Revenue", f"{month_rev:,.2f}")
                r3.metric("Last 7 Days Revenue", f"{week_rev:,.2f}")

                st.write("") # Adds a tiny spacer

                # --- SECTION 5: EXPENSE NUMERICALS ---
                st.write("#### 📉 Expense Details")
                e1, e2, e3 = st.columns(3)
                e1.metric("All-Time Expenses", f"{expense_df['Amount'].sum():,.2f}")
                e2.metric("This Month Expenses", f"{month_exp['Amount'].sum():,.2f}")
                e3.metric("Last 7 Days Expenses", f"{week_exp['Amount'].sum():,.2f}")

            except Exception as e:
                st.error(f"Financials waiting for data... ({e})")
if __name__ == "__main__":
    main()



































