import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="🏬 Retail Dashboard", layout="wide")
st.title("🏬 Retail Dashboard")

# ------------------------- Connect & Load Data -------------------------
conn = get_connection()
product_df = pd.read_sql("SELECT * FROM product", conn)
purchase_df = pd.read_sql("SELECT product_id, quantity_purchased, cost_price FROM purchases", conn)
sales_df = pd.read_sql("SELECT product_id, quantity_sold, selling_price FROM sales", conn)

# ------------------------- Aggregation -------------------------
purchase_agg = purchase_df.groupby('product_id').agg({
    'quantity_purchased': 'sum',
    'cost_price': 'mean'
}).reset_index()

sales_agg = sales_df.groupby('product_id').agg({
    'quantity_sold': 'sum',
    'selling_price': 'mean'
}).reset_index()

inventory_df = product_df.merge(purchase_agg, on='product_id', how='left')
inventory_df = inventory_df.merge(sales_agg, on='product_id', how='left')

inventory_df['quantity_purchased'] = inventory_df['quantity_purchased'].fillna(0)
inventory_df['quantity_sold'] = inventory_df['quantity_sold'].fillna(0)
inventory_df['cost_price'] = inventory_df['cost_price'].fillna(0)
inventory_df['selling_price'] = inventory_df['selling_price'].fillna(0)
inventory_df['initial_stock'] = inventory_df['stock'].fillna(0)

inventory_df['live_stock'] = (
    inventory_df['initial_stock'] +
    inventory_df['quantity_purchased'] -
    inventory_df['quantity_sold']
)

inventory_df['revenue'] = inventory_df['quantity_sold'] * inventory_df['selling_price']
inventory_df['profit'] = inventory_df['quantity_sold'] * (inventory_df['selling_price'] - inventory_df['cost_price'])

# ------------------------- KPI Section -------------------------
st.markdown("### 📊 Key Metrics")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("🧾 Total Products", len(inventory_df))
kpi2.metric("📦 Total Stock", int(inventory_df['live_stock'].sum()))
kpi3.metric("🛒 Units Sold", int(inventory_df['quantity_sold'].sum()))
kpi4.metric("💰 Total Revenue", f"₹ {inventory_df['revenue'].sum():,.2f}")
kpi5.metric("📈 Total Profit", f"₹ {inventory_df['profit'].sum():,.2f}")

# ------------------------- Low Stock Alerts -------------------------
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")

threshold = st.slider("Set stock threshold", min_value=1, max_value=50, value=10)
low_stock_df = inventory_df[inventory_df['live_stock'] < threshold]

if low_stock_df.empty:
    st.success("✅ All products have sufficient stock.")
else:
    st.error(f"⚠️ {len(low_stock_df)} products are below threshold")
    st.dataframe(low_stock_df[['product_id', 'product_name', 'category', 'live_stock']], use_container_width=True)

# ------------------------- Visual Insights -------------------------
st.markdown("---")
st.subheader("📊 Visual Insights")

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        inventory_df.sort_values(by='revenue', ascending=False).head(10),
        x='product_name', y='revenue',
        title="🔝 Top Products by Revenue", color='category',
        labels={'product_name': 'Product', 'revenue': '₹ Revenue'}
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    category_value = inventory_df.groupby('category')['live_stock'].sum().reset_index()
    fig2 = px.pie(category_value, names='category', values='live_stock', title="🧺 Stock Distribution by Category")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------- Monthly Trend (Optional) -------------------------
st.markdown("---")
st.subheader("📆 Monthly Sales Trend")

sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'])
sales_df['month'] = sales_df['sales_date'].dt.to_period('M').astype(str)
sales_df['revenue'] = sales_df['quantity_sold'] * sales_df['selling_price']

monthly_trend = sales_df.groupby('month').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum'
}).reset_index()

fig3 = px.line(monthly_trend, x='month', y=['quantity_sold', 'revenue'],
               title="📈 Sales & Revenue Trend Over Time",
               markers=True,
               labels={'value': 'Units / ₹', 'variable': 'Metric'})

st.plotly_chart(fig3, use_container_width=True)
