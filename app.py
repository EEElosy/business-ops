import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(layout="wide", page_title="Nibworks ERP ✒️")

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

    def load_sheet(self, sheet_name, required_cols):
        df = self.conn.read(worksheet=sheet_name, ttl=0)
        for col in required_cols:
            if col not in df.columns: df[col] = ""
        return df

    def load_inventory(self):
        df = self.load_sheet("Inventory", ["Date", "Brand", "Model", "Color", "Details", "Purchase Price", "Target Price", "Stock", "Supplier", "Currency"])
        df["Stock"] = pd.to_numeric(df["Stock"], errors='coerce').fillna(0)
        df["Purchase Price"] = pd.to_numeric(df["Purchase Price"], errors='coerce').fillna(0.0)
        df["Target Price"] = pd.to_numeric(df["Target Price"], errors='coerce').fillna(0.0)
        if "Currency" not in df.columns: df["Currency"] = "$" 
        return df

    def load_nib_orders(self):
        df = self.load_sheet("Nib Orders", ["Date", "Name", "Quantity", "Status", "Price", "Currency"])
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce').fillna(1)
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce').fillna(0.0)
        if "Currency" not in df.columns: df["Currency"] = "$"
        return df

    def update_sheet(self, sheet_name, dataframe):
        self.conn.update(worksheet=sheet_name, data=dataframe)

    # --- NIB ORDER ACTIONS ---
    def add_nib_order(self, df, order_data):
        updated_df = pd.concat([df, pd.DataFrame([order_data])], ignore_index=True)
        self.update_sheet("Nib Orders", updated_df)

    def update_nib_order(self, df, index, new_status, new_price):
        df.loc[index, "Status"] = new_status
        df.loc[index, "Price"] = float(new_price)
        self.update_sheet("Nib Orders", df)

    # --- STANDARD TRANSACTION LOGIC ---
    def register_sale(self, inventory_df, row_index, final_selling_price, sales_currency, exchange_rate):
        brand = inventory_df.loc[row_index, 'Brand']
        model = inventory_df.loc[row_index, 'Model']
        original_cost = float(inventory_df.loc[row_index, 'Purchase Price']) 
        
        normalized_cost = original_cost * exchange_rate
        item_name = f"{brand} {model}"
        current_stock = inventory_df.loc[row_index, "Stock"]
        
        if current_stock < 1: return False, "❌ Out of Stock!"

        inventory_df.loc[row_index, "Stock"] = current_stock - 1
        self.update_sheet("Inventory", inventory_df)

        try:
            sales_data = self.conn.read(worksheet="Sales", ttl=0)
        except:
            sales_data = pd.DataFrame(columns=["Date", "Item Sold", "Quantity", "Selling Price", "Currency", "Cost Price", "Exchange Rate"])

        new_sale = {
            "Date": str(date.today()), "Item Sold": item_name, "Quantity": 1,
            "Selling Price": float(final_selling_price), "Currency": sales_currency,
            "Cost Price": normalized_cost, "Exchange Rate": exchange_rate
        }
        updated_sales = pd.concat([sales_data, pd.DataFrame([new_sale])], ignore_index=True)
        self.update_sheet("Sales", updated_sales)
        return True, f"✅ Sold {item_name} for {final_selling_price} {sales_currency}!"

    def log_expense(self, category, amount, currency, notes):
        try:
            exp_data = self.conn.read(worksheet="Expenses", ttl=0)
        except:
            exp_data = pd.DataFrame(columns=["Date", "Category", "Amount", "Currency", "Notes"])
        new_expense = {"Date": str(date.today()), "Category": category, "Amount": float(amount), "Currency": currency, "Notes": notes}
        updated_exp = pd.concat([exp_data, pd.DataFrame([new_expense])], ignore_index=True)
        self.update_sheet("Expenses", updated_exp)
        return True

# --- MAIN APP ---
def main():
    if check_password():
        st.title("🏭 Operations & Service ERP")
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
                search = st.text_input("Find Item", placeholder="Search Brand, Model...")
                
                if search:
                    term = search.lower()
                    mask = (
                        inventory["Brand"].astype(str).str.lower().str.contains(term) |
                        inventory["Model"].astype(str).str.lower().str.contains(term)
                    )
                    results = inventory[mask]
                else:
                    results = inventory

                if not results.empty:
                    options = results.index.tolist()
                    def labeler(i):
                        row = results.loc[i]
                        return f"{row['Brand']} {row['Model']} ({row['Color']})"
                    
                    selected_idx = st.selectbox("Select Item", options, format_func=labeler)
                    
                    # --- NEGOTIATION ENGINE ---
                    row = results.loc[selected_idx]
                    cost = float(row["Purchase Price"])
                    target = float(row["Target Price"])
                    item_currency = row["Currency"] if "Currency" in row else "$"

                    st.info(f"📊 **Original Cost:** {cost} {item_currency} | **Target:** {target} {item_currency}")
                    
                    # 1. Price & Currency Input
                    col_p, col_c = st.columns([2, 1])
                    final_price = col_p.number_input("Final Agreed Price", value=target)
                    sales_curr = col_c.selectbox("Sales Currency", ["$", "€", "₺", "£"], index=["$", "€", "₺", "£"].index(item_currency) if item_currency in ["$", "€", "₺", "£"] else 0)
                    
                    # 2. Exchange Rate Logic (The Smart Part)
                    exchange_rate = 1.0
                    if sales_curr != item_currency:
                        st.write(f"⚠️ **Conversion Needed:** You are selling in **{sales_curr}**, but bought in **{item_currency}**.")
                        exchange_rate = st.number_input(f"Enter Exchange Rate (1 {item_currency} = ? {sales_curr})", value=1.0, format="%.4f")
                        
                        # Show the math
                        new_cost = cost * exchange_rate
                        st.caption(f"ℹ️ Normalized Cost: {cost} {item_currency} × {exchange_rate} = **{new_cost:.2f} {sales_curr}**")
                        
                        # Recalculate Logic for Warning
                        cost = new_cost 

                    # Margin Warning
                    if final_price < cost:
                        st.warning(f"⚠️ Loss Alert: Selling {cost - final_price:.2f} {sales_curr} below cost!")
                    else:
                        st.success(f"📈 Profit: {final_price - cost:.2f} {sales_curr}")

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
                    cat = st.selectbox("Category", ["Rent", "Electricity", "Marketing", "Salary", "Inventory Purchase", "Other"])
                    e_col1, e_col2 = st.columns([2, 1])
                    amt = e_col1.number_input("Amount", min_value=0.0)
                    curr = e_col2.selectbox("Currency", ["$", "€", "₺", "£"])
                    note = st.text_input("Note")
                    
                    if st.form_submit_button("Save Expense"):
                        db.log_expense(cat, amt, curr, note)
                        st.success("Expense Saved!")

        # --- TAB 2: NIB CUSTOMIZATION SERVICES ---
        with tab_nib:
            col_queue, col_new = st.columns([2, 1])
            
            with col_new:
                st.subheader("➕ New Nib Order")
                with st.form("new_nib"):
                    n_date = st.date_input("Order Date", value=date.today())
                    n_name = st.text_input("Customer/Order Name")
                    n_qty = st.number_input("Quantity", min_value=1, step=1)
                    n_price = st.number_input("Quoted Price", value=0.0)
                    n_curr = st.selectbox("Currency", ["$", "€", "₺", "£"])
                    
                    if st.form_submit_button("Create Order"):
                        if n_name:
                            db.add_nib_order(nib_orders, {
                                "Date": str(n_date), "Name": n_name, "Quantity": n_qty,
                                "Status": "In Progress", "Price": n_price, "Currency": n_curr
                            })
                            st.success("Order Added!")
                            st.rerun()
                        else:
                            st.warning("Name is required.")

            with col_queue:
                st.subheader("📋 Active Work Queue")
                active_mask = nib_orders["Status"] == "In Progress"
                active_orders = nib_orders[active_mask]
                
                if active_orders.empty:
                    st.success("All caught up! No active orders.")
                else:
                    for idx, row in active_orders.iterrows():
                        # Time Delta Calculation
                        order_date = datetime.strptime(str(row["Date"]), "%Y-%m-%d").date()
                        days_waiting = (date.today() - order_date).days
                        
                        # UI Card rendering
                        with st.container():
                            st.markdown(f"**{row['Name']}** | 📦 Qty: {row['Quantity']}")
                            st.markdown(f"🔴 *In Progress* — Waiting: **{days_waiting} days**")
                            
                            c_price, c_curr, c_btn = st.columns([2, 1, 1])
                            new_p = c_price.number_input("Price", value=float(row["Price"]), key=f"p_{idx}")
                            
                            if c_btn.button("✅ Mark Completed", key=f"btn_{idx}"):
                                db.update_nib_order(nib_orders, idx, "Completed", new_p)
                                st.rerun()
                            st.divider()

            st.subheader("✅ Completed Orders")
            completed_orders = nib_orders[nib_orders["Status"] == "Completed"]
            st.dataframe(completed_orders, use_container_width=True)

        # --- TAB 3: INVENTORY (Omitted for brevity, remains unchanged) ---
        with tab_inv:
            st.subheader("Current Stock")
            st.dataframe(inventory, use_container_width=True)
            
            with st.expander("➕ Add New Inventory"):
                with st.form("add_inv"):
                    c_date, c_brand, c_model = st.columns(3)
                    d = c_date.date_input("Date", value=date.today())
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
                    cur = c_cur.selectbox("Currency", ["$", "€", "₺", "£"])
                    
                    if st.form_submit_button("Save Item"):
                        new_item = {
                            "Date":str(d), "Brand":b, "Model":m, "Color":color, "Details":det,
                            "Purchase Price":cost_p, "Target Price":targ_p, 
                            "Stock":stk, "Supplier":sup, "Currency":cur
                        }
                        db.add_inventory_item(inventory, new_item)
                        st.success(f"Added {b} {m}!")
                        st.rerun()

        # --- TAB 4: REAL PROFIT & ANALYTICS ---
        with tab_finance:
            st.subheader("Profitability & Operational Volume")
            try:
                sales_df = db.load_sheet("Sales", ["Selling Price", "Cost Price", "Currency"])
                expense_df = db.load_sheet("Expenses", ["Amount", "Currency"])
                
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

