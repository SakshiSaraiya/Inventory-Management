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
# Compute live stock and total value
# -------------------------
inventory_df['live_stock'] = inventory_df['quantity_purchased'] - inventory_df['quantity_sold']
inventory_df['stock_value'] = inventory_df['live_stock'] * inventory_df['cost_price']
inventory_df['potential_revenue'] = inventory_df['live_stock'] * inventory_df['selling_price']
inventory_df['profit_margin'] = inventory_df['selling_price'] - inventory_df['cost_price']
inventory_df['total_profit'] = inventory_df['profit_margin'] * inventory_df['live_stock']

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
search_term = st.sidebar.text_input("Search Product")

filtered = inventory_df[inventory_df['Category'].isin(selected_category)]
if search_term:
    filtered = filtered[filtered['name'].str.contains(search_term, case=False)]

# -------------------------
# KPI Cards
# -------------------------
st.markdown("### 📊 Inventory KPIs")
k1, k2, k3, k4 = st.columns(4)
k1.metric("📦 Total Live Stock", int(filtered['live_stock'].sum()))
k2.metric("💰 Stock Value", f"₹ {filtered['stock_value'].sum():,.2f}")
k3.metric("📈 Revenue Potential", f"₹ {filtered['potential_revenue'].sum():,.2f}")
k4.metric("📐 Avg. Margin", f"₹ {filtered['profit_margin'].mean():.2f}")

# -------------------------
# Inventory Table
# -------------------------
st.markdown("### 📋 Product List (Live Stock)")
st.dataframe(
    filtered[['product_id', 'name', 'Category', 'Cost Price', 'Selling Price', 'live_stock', 'stock_value']],
    use_container_width=True
)

# -------------------------
# Low Stock Warning
# -------------------------
low_stock = filtered[filtered['live_stock'] < 10]

if not low_stock.empty:
    st.markdown("### ⚠️ Low Stock Alerts")
    st.error(f"⚠️ {low_stock.shape[0]} product(s) are low on stock")
    st.dataframe(low_stock[['product_id', 'name', 'Category', 'live_stock']], use_container_width=True)
else:
    st.success("✅ All filtered products are well stocked.")

# -------------------------
# Stock Value Visualization
# -------------------------
st.markdown("---")
st.markdown("### 💰 Stock Value by Category")

category_value = filtered.groupby('Category')['stock_value'].sum().reset_index()
fig = px.pie(category_value, names='Category', values='stock_value',
             title="Total Inventory Value by Category", template='plotly_dark', hole=0.4)
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Profit Opportunity Summary
# -------------------------
st.markdown("---")
st.markdown("### 📈 Profit Opportunity by Product")

top_n = st.slider("Top N Products by Profit", 5, 20, 10)
top_profit = filtered.sort_values(by='total_profit', ascending=False).head(top_n)

fig_profit = px.bar(top_profit, x='name', y='total_profit', color='profit_margin',
                    title=f"Top {top_n} Products by Profit Potential",
                    labels={'total_profit': 'Total Potential Profit', 'name': 'Product'},
                    template='plotly_dark')
fig_profit.update_layout(xaxis_title="Product", yaxis_title="Profit")
st.plotly_chart(fig_profit, use_container_width=True)

# -------------------------
# Stock Distribution by Product
# -------------------------
st.markdown("---")
st.markdown("### 📦 Stock Distribution by Product")

top_stock = st.slider("Top N Products by Stock", 5, 20, 10)
stock_bar = px.bar(
    filtered.sort_values(by='live_stock', ascending=False).head(top_stock),
    x='name', y='live_stock',
    title=f"Top {top_stock} Products by Live Stock",
    color='live_stock',
    template='plotly_dark'
)
stock_bar.update_layout(xaxis_title="Product", yaxis_title="Live Stock", showlegend=False)
st.plotly_chart(stock_bar, use_container_width=True)
