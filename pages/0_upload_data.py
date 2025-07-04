import streamlit as st
import pandas as pd
from db_connector import get_connection

st.title("📤 Upload or Add Inventory Data")

conn = get_connection()
if conn is None:
    st.stop()  # Prevent app from continuing if connection fails

cursor = conn.cursor()


st.markdown("### Upload CSV Files")

# --- INVENTORY UPLOAD ---
inventory_file = st.file_uploader("Upload Inventory CSV", type=["csv"])
if inventory_file:
    df = pd.read_csv(inventory_file)
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Products (name, category, variation, cost_price, selling_price, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, tuple(row))
    conn.commit()
    st.success("✅ Inventory data uploaded successfully!")

# --- SALES UPLOAD ---
sales_file = st.file_uploader("Upload Sales CSV", type=["csv"])
if sales_file:
    df = pd.read_csv(sales_file)
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Sales (product_id, quantity_sold, sale_date, shipped, payment_received)
            VALUES (%s, %s, %s, %s, %s)
        """, tuple(row))
    conn.commit()
    st.success("✅ Sales data uploaded successfully!")

# --- PURCHASE UPLOAD ---
purchase_file = st.file_uploader("Upload Purchases CSV", type=["csv"])
if purchase_file:
    df = pd.read_csv(purchase_file)
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Purchases (product_id, vendor_name, quantity_purchased, order_date, payment_due, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, tuple(row))
    conn.commit()
    st.success("✅ Purchase data uploaded successfully!")

# --- MANUAL ENTRY SECTION ---
st.markdown("### 📋 Add Data Manually")

# --- Add Product ---
with st.expander("➕ Add New Product"):
    with st.form("add_product_form"):
        product_id = st.number_input("Product ID", min_value=1)
        name = st.text_input("Product Name")
        category = st.text_input("Category")
        variation = st.text_input("Variation")
        cost_price = st.number_input("Cost Price", min_value=0.0)
        selling_price = st.number_input("Selling Price", min_value=0.0)
        stock = st.number_input("Stock Quantity", min_value=0)
        submit = st.form_submit_button("Add Product")

        if submit:
            try:
                # Check for duplicate product_id
                cursor.execute("SELECT 1 FROM Products WHERE product_id = %s", (product_id,))
                if cursor.fetchone():
                    st.error(f"❌ Product ID {product_id} already exists.")
                else:
                    cursor.execute("""
                        INSERT INTO Products (product_id, name, category, variation, cost_price, selling_price, stock)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (product_id, name, category, variation, cost_price, selling_price, stock))
                    conn.commit()
                    st.success("✅ Product added successfully!")
                    st.info("➕ You can add more products using the form above.")
            except Exception as e:
                st.error("❌ Failed to insert product.")
                st.code(str(e))

#--- Add Sales---
with st.expander("➕ Add New Sale"):
    with st.form("add_sale_form"):
        sale_id = st.number_input("Sale ID", min_value=1)
        product_id = st.number_input("Product ID (for sale)", min_value=1)
        quantity_sold = st.number_input("Quantity Sold", min_value=1)
        sale_date = st.date_input("Sale Date")
        shipped = st.checkbox("Shipped?")
        payment_received = st.checkbox("Payment Received?")
        submit_sale = st.form_submit_button("Add Sale")

        if submit_sale:
            cursor.execute("SELECT 1 FROM Sales WHERE sale_id = %s", (sale_id,))
            if cursor.fetchone():
                st.error(f"❌ Sale ID {sale_id} already exists. Choose a different ID.")
            else:
                cursor.execute("SELECT 1 FROM Products WHERE product_id = %s", (product_id,))
                if cursor.fetchone() is None:
                    st.error(f"❌ Product ID {product_id} does not exist.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Sales (sale_id, product_id, quantity_sold, sale_date, shipped, payment_received)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (sale_id, product_id, quantity_sold, sale_date, shipped, payment_received))
                        conn.commit()
                        st.success("✅ Sale added successfully!")
                    except Exception as e:
                        st.error("❌ Failed to insert sale.")
                        st.code(str(e))


# --- Add Purchase ---
with st.expander("➕ Add New Purchase"):
    with st.form("add_purchase_form"):
        purchase_id = st.number_input("Purchase ID", min_value=1)
        product_id = st.number_input("Product ID (for purchase)", min_value=1)
        vendor = st.text_input("Vendor Name")
        quantity = st.number_input("Quantity Purchased", min_value=1)
        order_date = st.date_input("Order Date")
        payment_due = st.date_input("Payment Due Date")
        payment_status = st.selectbox("Payment Status", ["Pending", "Paid", "Overdue"])
        submit_purchase = st.form_submit_button("Add Purchase")

        if submit_purchase:
            cursor.execute("SELECT 1 FROM Purchases WHERE purchase_id = %s", (purchase_id,))
            if cursor.fetchone():
                st.error(f"❌ Purchase ID {purchase_id} already exists. Choose a different ID.")
            else:
                cursor.execute("SELECT 1 FROM Products WHERE product_id = %s", (product_id,))
                if cursor.fetchone() is None:
                    st.error(f"❌ Product ID {product_id} does not exist.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Purchases (purchase_id, product_id, vendor_name, quantity_purchased, order_date, payment_due, payment_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (purchase_id, product_id, vendor, quantity, order_date, payment_due, payment_status))
                        conn.commit()
                        st.success("✅ Purchase added successfully!")
                    except Exception as e:
                        st.error("❌ Failed to insert purchase.")
                        st.code(str(e))


