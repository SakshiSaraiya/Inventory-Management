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
purchases_df = pd.read_sql("SELECT product_id, quantity_purchased, cost_price, order_date FROM purchases", conn)
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

total_stock_value = total_stock['quantity_purchased'].sum() - total_stock['quantity_sold'].sum()
total_units_sold = sales_df['quantity_sold'].sum()
total_revenue = (sales_df['quantity_sold'] * sales_df['selling_price']).sum()

# Merge cost price for profit
sales_merged = sales_df.merge(purchases_df[['product_id', 'cost_price']], on='product_id', how='left')
sales_merged['profit'] = sales_merged['quantity_sold'] * (sales_merged['selling_price'] - sales_merged['cost_price'])
total_profit = sales_merged['profit'].sum()

# ----------------------
# KPI Cards
# ----------------------
st.markdown("### 📌 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🧮 Total Products", total_products)
with col2:
    st.metric("📦 Total Stock", int(total_stock_value))
with col3:
    st.metric("📈 Total Units Sold", int(total_units_sold))
with col4:
    st.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
with col5:
    st.metric("📊 Total Profit", f"₹ {total_profit:,.2f}")

# ----------------------
# Low Stock Alerts
# ----------------------
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")
threshold = st.slider("Set stock threshold", 1, 50, 10)

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
    st.error(f"⚠️ {len(low_stock_items)} product(s) are low on stock.")
    st.dataframe(low_stock_items[['product_id', 'product_name', 'live_stock']], use_container_width=True)
else:
    st.success("✅ All products have sufficient stock.")

# ----------------------
# Monthly Trend Charts
# ----------------------
st.markdown("---")
st.subheader("📅 Monthly Sales Trends")

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

fig = px.line(monthly, x='month', y=['quantity_sold', 'revenue', 'profit'],
              title="📊 Monthly Sales Overview",
              markers=True)
fig.update_layout(
    legend_title_text='Metrics',
    xaxis_title="Month",
    yaxis_title="Amount",
    template="plotly_white",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------
# Sales by Top Products
# ----------------------
st.markdown("---")
st.subheader("🏆 Top Selling Products")

top_products = sales_df.groupby('product_id')['quantity_sold'].sum().reset_index()
top_products = top_products.merge(product_df[['product_id', 'product_name']], on='product_id', how='left')
top_products = top_products.sort_values(by='quantity_sold', ascending=False).head(10)

bar_fig = px.bar(top_products, x='product_name', y='quantity_sold',
                 title="Top 10 Products by Units Sold",
                 color='quantity_sold', text='quantity_sold')
bar_fig.update_layout(xaxis_title="Product", yaxis_title="Units Sold", template="plotly_dark")
bar_fig.update_traces(textposition='outside')

st.plotly_chart(bar_fig, use_container_width=True)
