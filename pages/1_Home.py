import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📊 Retail Dashboard", layout="wide")
st.title("🏢 Retail Dashboard")

# Connect to MySQL
conn = get_connection()

# Load data from DB
try:
    product_df = pd.read_sql("SELECT * FROM product", conn)
    purchase_df = pd.read_sql("SELECT product_id, quantity_purchased, cost_price FROM purchases", conn)
    sales_df = pd.read_sql("SELECT * FROM sales", conn)
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# Merge & Compute Inventory
purchase_agg = purchase_df.groupby('product_id').agg({'quantity_purchased': 'sum', 'cost_price': 'mean'}).reset_index()
sales_agg = sales_df.groupby('product_id').agg({'quantity_sold': 'sum', 'selling_price': 'mean'}).reset_index()

inventory_df = product_df.merge(purchase_agg, on='product_id', how='left')
inventory_df = inventory_df.merge(sales_agg, on='product_id', how='left')

inventory_df['quantity_purchased'] = inventory_df['quantity_purchased'].fillna(0)
inventory_df['quantity_sold'] = inventory_df['quantity_sold'].fillna(0)
inventory_df['cost_price'] = inventory_df['cost_price'].fillna(0)
inventory_df['selling_price'] = inventory_df['selling_price'].fillna(0)

inventory_df['live_stock'] = inventory_df['quantity_purchased'] - inventory_df['quantity_sold']

# Calculate Revenue and Profit in sales_df
sales_df = sales_df.merge(purchase_agg[['product_id', 'cost_price']], on='product_id', how='left')
sales_df['revenue'] = sales_df['quantity_sold'] * sales_df['selling_price']
sales_df['profit'] = sales_df['revenue'] - (sales_df['quantity_sold'] * sales_df['cost_price'])

# ========================
# KPI SECTION
# ========================
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("🥚 Total Products", product_df.shape[0])
kpi2.metric("📺 Total Stock", int(inventory_df['live_stock'].sum()))
kpi3.metric("📊 Total Units Sold", int(sales_df['quantity_sold'].sum()))
kpi4.metric("💰 Total Revenue", f"₹ {sales_df['revenue'].sum():,.2f}")
kpi5.metric("📊 Total Profit", f"₹ {sales_df['profit'].sum():,.2f}")

st.markdown("""---""")

# ========================
# LOW STOCK ALERTS
# ========================
st.subheader(":red[🚨 Low Stock Alerts]")
threshold = st.slider("Set stock threshold", min_value=1, max_value=50, value=10)
low_stock_df = inventory_df[inventory_df['live_stock'] < threshold]

if not low_stock_df.empty:
    st.warning(f"⚠️ {low_stock_df.shape[0]} products are low on stock.")
    st.dataframe(low_stock_df[['product_id', 'product_name', 'live_stock']])
else:
    st.success("✅ All products have sufficient stock.")

st.markdown("""---""")

# ========================
# MONTHLY SALES TREND
# ========================
st.subheader("🗓️ Monthly Sales Trend")

try:
    sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'], errors='coerce')
    sales_df['month'] = sales_df['sales_date'].dt.to_period('M').astype(str)
    monthly = sales_df.groupby('month')[['quantity_sold', 'revenue', 'profit']].sum().reset_index()

    fig = px.line(monthly, x='month', y=['quantity_sold', 'revenue', 'profit'],
                  markers=True, title="Monthly Sales Overview")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error rendering monthly chart: {e}")
