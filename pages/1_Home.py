import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📊 Retail Dashboard", layout="wide")
st.title("🛒 Retail Dashboard")

# ----------------------
# Connect to SQL
# ----------------------
conn = get_connection()

# Load tables
product_df = pd.read_sql("SELECT * FROM product", conn)
purchases_df = pd.read_sql("SELECT product_id, quantity_purchased, cost_price, purchase_date FROM purchases", conn)
sales_df = pd.read_sql("SELECT product_id, quantity_sold, selling_price, sales_date FROM sales", conn)

# ----------------------
# Compute Metrics
# ----------------------
total_products = product_df['product_id'].nunique()

# Aggregate stock from purchases and sales
total_stock = purchases_df.groupby('product_id')['quantity_purchased'].sum().reset_index().merge(
    sales_df.groupby('product_id')['quantity_sold'].sum().reset_index(),
    on='product_id', how='outer'
).fillna(0)

if 'quantity_purchased' in total_stock.columns and 'quantity_sold' in total_stock.columns:
    total_stock_value = total_stock['quantity_purchased'].sum() - total_stock['quantity_sold'].sum()
else:
    total_stock_value = product_df['stock'].sum()

total_units_sold = sales_df['quantity_sold'].sum()
total_revenue = (sales_df['quantity_sold'] * sales_df['selling_price']).sum()

# Merge cost price for profit
sales_merged = sales_df.merge(purchases_df[['product_id', 'cost_price']], on='product_id', how='left')
sales_merged['profit'] = sales_merged['quantity_sold'] * (sales_merged['selling_price'] - sales_merged['cost_price'])
total_profit = sales_merged['profit'].sum()

# ----------------------
# KPI Cards
# ----------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("📦 Total Products", total_products)
col2.metric("📦 Total Stock", int(total_stock_value))
col3.metric("📈 Total Units Sold", int(total_units_sold))
col4.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
col5.metric("🧾 Total Profit", f"₹ {total_profit:,.2f}")

# ----------------------
# Low Stock Alerts
# ----------------------
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")

threshold = st.slider("Set stock threshold", 1, 50, 10)

# Live inventory
inventory = product_df.copy()
inventory = inventory.merge(
    purchases_df.groupby('product_id')['quantity_purchased'].sum(),
    on='product_id', how='left'
)
inventory = inventory.merge(
    sales_df.groupby('product_id')['quantity_sold'].sum(),
    on='product_id', how='left'
)

inventory['quantity_purchased'].fillna(0, inplace=True)
inventory['quantity_sold'].fillna(0, inplace=True)
inventory['live_stock'] = inventory['quantity_purchased'] - inventory['quantity_sold']

low_stock_items = inventory[inventory['live_stock'] < threshold]

if not low_stock_items.empty:
    st.error(f"⚠️ {len(low_stock_items)} products are low on stock.")
    st.dataframe(low_stock_items[['product_id', 'product_name', 'live_stock']])
else:
    st.success("✅ All products have sufficient stock.")

# ----------------------
# Monthly Trend Charts
# ----------------------
st.markdown("---")
st.subheader("📅 Monthly Sales Trend")

sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'], errors='coerce')
sales_df.dropna(subset=['sales_date'], inplace=True)
sales_df['month'] = sales_df['sales_date'].dt.to_period('M').astype(str)

monthly = sales_df.groupby('month').agg({
    'quantity_sold': 'sum',
    'selling_price': 'mean'
}).reset_index()
monthly['revenue'] = monthly['quantity_sold'] * monthly['selling_price']

# Profit per month
sales_df = sales_df.merge(purchases_df[['product_id', 'cost_price']], on='product_id', how='left')
sales_df['profit'] = sales_df['quantity_sold'] * (sales_df['selling_price'] - sales_df['cost_price'])
sales_df['month'] = sales_df['sales_date'].dt.to_period('M').astype(str)
monthly_profit = sales_df.groupby('month')['profit'].sum().reset_index()
monthly = monthly.merge(monthly_profit, on='month', how='left')

fig = px.bar(monthly, x='month', y=['quantity_sold', 'revenue', 'profit'],
             barmode='group', title="Monthly Sales Overview")
st.plotly_chart(fig, use_container_width=True)
