import streamlit as st 
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📦 Inventory", layout="wide")
st.title("📦 Inventory Overview")

# -------------------------
# Connect to SQL
# -------------------------
conn = get_connection()

# -------------------------
# Load data
# -------------------------
try:
    purchases = pd.read_sql("SELECT product_id, product_name, category, quantity_purchased, cost_price FROM purchases", conn)
    sales = pd.read_sql("SELECT product_id, quantity_sold, selling_price FROM sales", conn)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Normalize product_id
purchases['product_id'] = purchases['product_id'].astype(str).str.strip().str.upper()
sales['product_id'] = sales['product_id'].astype(str).str.strip().str.upper()

# -------------------------
# Aggregate stock and prices
# -------------------------
purchase_agg = purchases.groupby(['product_id', 'product_name', 'category']).agg({
    'quantity_purchased': 'sum',
    'cost_price': 'mean'
}).reset_index()

sales_agg = sales.groupby('product_id').agg({
    'quantity_sold': 'sum',
    'selling_price': 'mean'
}).reset_index()

# -------------------------
# Merge aggregated data
# -------------------------
inventory_df = purchase_agg.merge(sales_agg, on='product_id', how='left')

# Fill NaNs
inventory_df['quantity_sold'] = inventory_df['quantity_sold'].fillna(0)
inventory_df['selling_price'] = inventory_df['selling_price'].fillna(0)

# -------------------------
# Compute live stock
# -------------------------
inventory_df['live_stock'] = inventory_df['quantity_purchased'] - inventory_df['quantity_sold']

# -------------------------
# Rename for UI
# -------------------------
inventory_df.rename(columns={
    'product_name': 'name',
    'category': 'Category',
    'cost_price': 'Cost Price',
    'selling_price': 'Selling Price'
}, inplace=True)

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("🔍 Filter Inventory")

categories = inventory_df['Category'].dropna().unique()
selected_category = st.sidebar.multiselect("Category", categories, default=list(categories))

filtered = inventory_df[inventory_df['Category'].isin(selected_category)]

# -------------------------
# Inventory Table
# -------------------------
st.subheader("📋 Product List (Live Stock)")

st.dataframe(
    filtered[['product_id', 'name', 'Category', 'Cost Price', 'Selling Price', 'live_stock']],
    use_container_width=True
)

# -------------------------
# Low Stock Warning
# -------------------------
low_stock = filtered[filtered['live_stock'] < 10]

if not low_stock.empty:
    st.error(f"⚠️ {low_stock.shape[0]} products are low on stock")
    st.dataframe(low_stock[['product_id', 'name', 'Category', 'live_stock']])
else:
    st.success("✅ All filtered products are well stocked.")

# -------------------------
# Stock Value Visualization
# -------------------------
st.markdown("---")
st.subheader("💰 Stock Value by Category")

filtered['Stock Value'] = filtered['live_stock'] * filtered['Cost Price']
category_value = filtered.groupby('Category')['Stock Value'].sum().reset_index()

fig = px.pie(category_value, names='Category', values='Stock Value',
             title="Total Inventory Value by Category")
st.plotly_chart(fig, use_container_width=True)
