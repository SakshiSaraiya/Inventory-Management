import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection
from datetime import datetime

st.set_page_config(page_title="📊 Retail Dashboard", layout="wide")
st.title("📊 Retail Dashboard")

# -------------------------
# Database connection
# -------------------------
conn = get_connection()

# Load Data
try:
    product_df = pd.read_sql("SELECT * FROM product", conn)
    purchase_df = pd.read_sql("SELECT * FROM purchases", conn)
    sales_df = pd.read_sql("SELECT * FROM sales", conn)
except Exception as e:
    st.error(f"Database Load Error: {e}")
    st.stop()

# -------------------------
# Data Preparation
# -------------------------
purchase_df.fillna(0, inplace=True)
sales_df.fillna(0, inplace=True)

# Merge for product info
total_stock = purchase_df.groupby('product_id')['quantity_purchased'].sum() - \
              sales_df.groupby('product_id')['quantity_sold'].sum()
total_stock = total_stock.reset_index().rename(columns={0: 'live_stock'})

# KPIs
total_products = product_df.shape[0]
total_units_sold = sales_df['quantity_sold'].sum()
total_revenue = (sales_df['quantity_sold'] * sales_df['selling_price']).sum()

# Merge cost price info for profit calc
sales_profit_df = sales_df.merge(purchase_df[['product_id', 'cost_price']], on='product_id', how='left')
total_profit = ((sales_profit_df['selling_price'] - sales_profit_df['cost_price']) * sales_profit_df['quantity_sold']).sum()

# -------------------------
# KPI Cards
# -------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("📦 Total Products", total_products)
col2.metric("📦 Total Stock", int(total_stock['quantity_purchased'].sum() - total_stock['quantity_sold'].sum()))
col3.metric("📈 Total Units Sold", int(total_units_sold))
col4.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
col5.metric("🧾 Total Profit", f"₹ {total_profit:,.2f}")

# -------------------------
# Low Stock Alerts
# -------------------------
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")

threshold = st.slider("Set stock threshold", min_value=1, max_value=50, value=10)

inventory_df = product_df.merge(total_stock, on='product_id', how='left')
low_stock_df = inventory_df[inventory_df['live_stock'] < threshold]

if not low_stock_df.empty:
    st.error(f"⚠️ {low_stock_df.shape[0]} products are low on stock.")
    st.dataframe(low_stock_df[['product_id', 'product_name', 'live_stock']])
else:
    st.success("✅ All products have sufficient stock.")

# -------------------------
# Insights Summary (Mockup Style)
# -------------------------
st.markdown("---")
st.subheader("📊 Quick Insights")
col1, col2, col3 = st.columns(3)

# Best-Selling Product
top_product = sales_df.groupby('product_id')['quantity_sold'].sum().reset_index()
top_product = top_product.merge(product_df[['product_id', 'product_name']], on='product_id', how='left')
top_product = top_product.sort_values(by='quantity_sold', ascending=False).head(1)

if not top_product.empty:
    col1.markdown("🔥 **Best-Selling Product This Week**")
    col1.markdown(f"**{top_product['product_name'].values[0]}** ({top_product['quantity_sold'].values[0]} pcs)")

# Most Profitable Category
sales_profit_df = sales_profit_df.merge(product_df[['product_id', 'category']], on='product_id', how='left')
category_profit = sales_profit_df.groupby('category').apply(
    lambda x: ((x['selling_price'] - x['cost_price']) * x['quantity_sold']).sum()
).reset_index(name='total_profit')
most_prof_cat = category_profit.sort_values(by='total_profit', ascending=False).head(1)

if not most_prof_cat.empty:
    col2.markdown("📊 **Most Profitable Category**")
    col2.markdown(f"**{most_prof_cat['category'].values[0]}** (₹ {most_prof_cat['total_profit'].values[0]:,.0f})")

# Sales Trend Summary
sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'], errors='coerce')
sales_df['week'] = sales_df['sales_date'].dt.to_period('W').astype(str)
weekly_sales = sales_df.groupby('week')['quantity_sold'].sum().reset_index()
if len(weekly_sales) >= 2:
    delta = weekly_sales.iloc[-1]['quantity_sold'] - weekly_sales.iloc[-2]['quantity_sold']
    percent_change = (delta / weekly_sales.iloc[-2]['quantity_sold']) * 100 if weekly_sales.iloc[-2]['quantity_sold'] != 0 else 0
    col3.markdown("📈 **Sales Trend**")
    col3.markdown(f"↑ {percent_change:.0f}% vs Last Week")

# -------------------------
# Visual Insights
# -------------------------
st.markdown("---")
st.subheader("📊 Visual Insights")

# Category-wise revenue
sales_df['revenue'] = sales_df['quantity_sold'] * sales_df['selling_price']
sales_df = sales_df.merge(product_df[['product_id', 'category']], on='product_id', how='left')
category_revenue = sales_df.groupby('category')['revenue'].sum().reset_index().sort_values(by='revenue', ascending=False)

fig = px.bar(category_revenue, x='category', y='revenue', title="Revenue by Category", color='category')
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Monthly Sales Trend
# -------------------------
st.subheader("📆 Monthly Sales Trend")
sales_df['month'] = sales_df['sales_date'].dt.to_period('M').astype(str)
monthly = sales_df.groupby('month').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'product_id': 'count'
}).reset_index().rename(columns={'product_id': 'transactions'})

fig2 = px.line(monthly, x='month', y=['quantity_sold', 'revenue'], title="Monthly Quantity Sold & Revenue")
st.plotly_chart(fig2, use_container_width=True)
