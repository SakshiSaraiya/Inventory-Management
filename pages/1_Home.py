import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection, fetch_query

st.set_page_config(page_title="📊 Dashboard", layout="wide")
st.title("📊 Retail Dashboard")

# Connect to DB
conn = get_connection()
cursor = conn.cursor(dictionary=True)

# Load data
products = pd.read_sql("SELECT * FROM product", conn)
sales = pd.read_sql("SELECT * FROM sales", conn)
purchases = pd.read_sql("SELECT * FROM purchases", conn)

# Merge sales with purchase info (for cost_price & product name)
merged = pd.merge(sales, purchases[['product_id', 'cost_price', 'product_name']], on='product_id', how='left')

# Calculate revenue and profit
merged['revenue'] = merged['quantity_sold'] * merged['selling_price']
merged['profit'] = merged['quantity_sold'] * (merged['selling_price'] - merged['cost_price'])

# KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🧺 Total Products", products['product_id'].nunique())
col2.metric("📦 Total Stock", products['stock'].sum())
col3.metric("🛒 Total Units Sold", sales['quantity_sold'].sum())
col4.metric("💰 Total Revenue", f"₹ {merged['revenue'].sum():,.2f}")
col5.metric("📈 Total Profit", f"₹ {merged['profit'].sum():,.2f}")

# Low Stock Alerts
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")
threshold = st.slider("Set stock threshold", min_value=1, max_value=50, value=10)

low_stock = products[products['stock'] < threshold]
if not low_stock.empty:
    st.error("⚠️ The following products are running low on stock:")
    st.dataframe(low_stock[['product_id', 'product_name', 'category', 'stock']])
else:
    st.success("✅ All products have sufficient stock.")

# Sales Trend Over Time
st.markdown("---")
st.subheader("📈 Monthly Sales Trend")

merged['sales_date'] = pd.to_datetime(merged['sales_date'], errors='coerce')
merged = merged.dropna(subset=['sales_date'])

merged['month'] = merged['sales_date'].dt.to_period('M').astype(str)

monthly = merged.groupby('month').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'profit': 'sum'
}).reset_index()

tab1, tab2, tab3 = st.tabs(["📦 Quantity Sold", "💰 Revenue", "📈 Profit"])

with tab1:
    st.bar_chart(monthly.set_index('month')['quantity_sold'])

with tab2:
    st.line_chart(monthly.set_index('month')['revenue'])

with tab3:
    st.area_chart(monthly.set_index('month')['profit'])
