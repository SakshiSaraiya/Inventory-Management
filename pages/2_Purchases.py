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

# Convert date columns
purchases['order_date'] = pd.to_datetime(purchases['order_date'], errors='coerce')
purchases['payment_due_date'] = pd.to_datetime(purchases['payment_due_date'], errors='coerce')

# -------------------------
# Compute KPIs
# -------------------------
total_orders = purchases['purchase_id'].nunique()
total_quantity = purchases['quantity_purchased'].sum()
total_cost = (purchases['quantity_purchased'] * purchases['cost_price']).sum()
vendors = purchases['vendor_name'].nunique()

# -------------------------
# KPI Display
# -------------------------
st.markdown("### 🚀 Key Purchase Metrics")
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("📆 Total Orders", total_orders)
with k2:
    st.metric("🛋️ Units Purchased", int(total_quantity))
with k3:
    st.metric("💸 Total Spend", f"₹ {total_cost:,.2f}")
with k4:
    st.metric("💼 Vendors", vendors)

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
st.markdown("### 📦 Purchase Records")
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
st.markdown("### ⚠️ Payment Alerts")

today = pd.to_datetime("today")
pending = filtered[filtered['payment_status'].str.lower() == "pending"]
overdue = filtered[(filtered['payment_status'].str.lower() != "paid") & (filtered['payment_due_date'] < today)]

col1, col2 = st.columns(2)

with col1:
    st.warning(f"🕐 Pending Payments: {len(pending)}")
    if not pending.empty:
        st.dataframe(pending[['vendor_name', 'product_name', 'payment_due_date']], use_container_width=True)

with col2:
    st.error(f"❌ Overdue Payments: {len(overdue)}")
    if not overdue.empty:
        st.dataframe(overdue[['vendor_name', 'product_name', 'payment_due_date']], use_container_width=True)

# -------------------------
# Vendor-wise Purchases
# -------------------------
st.markdown("---")
st.markdown("### 🏢 Vendor-wise Purchases")

vendor_summary = filtered.groupby('vendor_name')['quantity_purchased'].sum().reset_index()
fig_vendor = px.bar(
    vendor_summary,
    x='vendor_name',
    y='quantity_purchased',
    title="📊 Quantity Purchased by Vendor",
    color='quantity_purchased',
    text='quantity_purchased',
    template='plotly_dark'
)
fig_vendor.update_traces(textposition="outside")
fig_vendor.update_layout(xaxis_title="Vendor", yaxis_title="Quantity", showlegend=False)
st.plotly_chart(fig_vendor, use_container_width=True)

# -------------------------
# Monthly Purchase Trend
# -------------------------
st.markdown("---")
st.markdown("### 📆 Monthly Purchase Trend")

filtered['month'] = filtered['order_date'].dt.to_period('M').astype(str)
monthly_summary = filtered.groupby('month')['quantity_purchased'].sum().reset_index()

fig_monthly = px.line(
    monthly_summary,
    x='month',
    y='quantity_purchased',
    title="📈 Monthly Purchase Volume",
    markers=True,
    template='plotly_dark'
)
fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Quantity Purchased")
st.plotly_chart(fig_monthly, use_container_width=True)

# -------------------------
# Purchase Breakdown by Product
# -------------------------
st.markdown("---")
st.markdown("### 📟 Product-wise Purchase Summary")

product_summary = filtered.groupby('product_name')['quantity_purchased'].sum().reset_index().sort_values(by='quantity_purchased', ascending=False)
fig_product = px.bar(
    product_summary,
    x='product_name',
    y='quantity_purchased',
    title="Top Products by Purchase Volume",
    color='quantity_purchased',
    template='plotly_dark'
)
fig_product.update_layout(xaxis_title="Product", yaxis_title="Quantity", showlegend=False)
st.plotly_chart(fig_product, use_container_width=True)
