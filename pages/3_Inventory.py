import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📦 Inventory", layout="wide")
st.title("📦 Inventory Overview")

# Connect to SQL
conn = get_connection()

# Load product data
products = pd.read_sql("SELECT * FROM Products", conn)

# -------------------------
# Filters
# -------------------------
st.sidebar.header("🔍 Filter Inventory")

categories = products['category'].dropna().unique()
selected_category = st.sidebar.multiselect("Category", categories, default=list(categories))

variations = products['variation'].dropna().unique()
selected_variation = st.sidebar.multiselect("Variation", variations, default=list(variations))

filtered = products[
    products['category'].isin(selected_category) &
    products['variation'].isin(selected_variation)
]

# -------------------------
# Inventory Table
# -------------------------
st.subheader("📋 Product List")

st.dataframe(
    filtered[['product_id', 'name', 'category', 'variation', 'cost_price', 'selling_price', 'stock']],
    use_container_width=True
)

# -------------------------
# Low Stock Highlight
# -------------------------
low_stock = filtered[filtered['stock'] < 10]

if not low_stock.empty:
    st.error(f"⚠️ {low_stock.shape[0]} products are low on stock")
    st.dataframe(low_stock[['product_id', 'name', 'category', 'variation', 'stock']])
else:
    st.success("✅ All filtered products are well stocked.")

# -------------------------
# Stock Value by Category
# -------------------------
st.markdown("---")
st.subheader("💰 Stock Value by Category")

filtered['stock_value'] = filtered['stock'] * filtered['cost_price']
category_value = filtered.groupby('category')['stock_value'].sum().reset_index()

fig = px.pie(category_value, names='category', values='stock_value',
             title="Total Inventory Value by Category")
st.plotly_chart(fig, use_container_width=True)
