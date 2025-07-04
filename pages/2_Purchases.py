import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📥 Purchases", layout="wide")
st.title("📥 Purchase Overview")

# -------------------------
# Connect to SQL
# -------------------------
conn = get_connection()

# -------------------------
# Load Data from SQL
# -------------------------
purchases = pd.read_sql("SELECT * FROM purchases", conn)

# Debug: Show actual columns
# st.write("📋 Columns in purchases table:", purchases.columns.tolist())

# Convert date columns
purchases['order_date'] = pd.to_datetime(purchases['order_date'], errors='coerce')
purchases['payment_due_date'] = pd.to_datetime(purchases['payment_due_date'], errors='coerce')

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("🔍 Filter Purchases")

product_filter = st.sidebar.multiselect(
    "Product", purchases['product_name'].dropna().unique(), default=purchases['product_name'].unique()
)
vendor_filter = st.sidebar.multiselect(
    "Vendor", purchases['vendor_name'].dropna().unique(), default=purchases['vendor_name'].unique()
)
status_filter = st.sidebar.multiselect(
    "Payment Status", purchases['payment_status'].dropna().unique(), default=purchases['payment_status'].unique()
)
start_date = st.sidebar.date_input("Start Date", purchases['order_date'].min())
end_date = st.sidebar.date_input("End Date", purchases['order_date'].max())

# Apply filters
filtered = purchases[
    (purchases['product_name'].isin(product_filter)) &
    (purchases['vendor_name'].isin(vendor_filter)) &
    (purchases['payment_status'].isin(status_filter)) &
    (purchases['order_date'] >= pd.to_datetime(start_date)) &
    (purchases['order_date'] <= pd.to_datetime(end_date))
]

# -------------------------
# Display Filtered Table
# -------------------------
st.subheader("📋 Purchase Records")

# Show only available columns (defensive programming)
expected_cols = [
    'purchase_id', 'product_id', 'product_name', 'vendor_name',
    'quantity_purchased', 'cost_price', 'order_date', 'payment_due_date', 'payment_status'
]
available_cols = [col for col in expected_cols if col in filtered.columns]
st.dataframe(filtered[available_cols], use_container_width=True)

# -------------------------
# Payment Alerts
# -------------------------
st.markdown("---")
st.subheader("⚠️ Payment Alerts")

today = pd.to_datetime("today")
pending = filtered[filtered['payment_status'].str.lower() == "pending"]
overdue = filtered[(filtered['payment_status'].str.lower() != "paid") & (filtered['payment_due_date'] < today)]

col1, col2 = st.columns(2)

with col1:
    st.warning(f"🕐 Pending Payments: {len(pending)}")
    if not pending.empty:
        st.dataframe(pending[['vendor_name', 'product_name', 'payment_due_date']])

with col2:
    st.error(f"❌ Overdue Payments: {len(overdue)}")
    if not overdue.empty:
        st.dataframe(overdue[['vendor_name', 'product_name', 'payment_due_date']])

# -------------------------
# Vendor-wise Purchases
# -------------------------
st.markdown("---")
st.subheader("🏢 Vendor-wise Purchases")

vendor_summary = filtered.groupby('vendor_name')['quantity_purchased'].sum().reset_index()
fig_vendor = px.bar(vendor_summary, x='vendor_name', y='quantity_purchased', title="Quantity Purchased by Vendor")
st.plotly_chart(fig_vendor, use_container_width=True)

# -------------------------
# Monthly Purchase Trend
# -------------------------
st.subheader("📆 Monthly Purchase Trend")

filtered['month'] = filtered['order_date'].dt.to_period('M').astype(str)
monthly_summary = filtered.groupby('month')['quantity_purchased'].sum().reset_index()

fig_monthly = px.line(monthly_summary, x='month', y='quantity_purchased', title="Monthly Purchase Volume")
st.plotly_chart(fig_monthly, use_container_width=True)
