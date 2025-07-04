import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📊 Retail Dashboard", layout="wide")
st.title("📊 Retail Dashboard")

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
# KPI Cards with Emojis
# ----------------------
st.markdown("### 🚀 Key Performance Metrics")
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(label="🧾 Total Products", value=total_products)
with k2:
    st.metric(label="📦 Total Stock", value=int(total_stock_value))
with k3:
    st.metric(label="📈 Units Sold", value=int(total_units_sold))
with k4:
    st.metric(label="💰 Total Revenue", value=f"₹ {total_revenue:,.2f}")
with k5:
    st.metric(label="🧮 Total Profit", value=f"₹ {total_profit:,.2f}")

# ----------------------
# Highlights Section
# ----------------------
st.markdown("---")
st.markdown("### 🔥 Highlights")

# Best Selling Product
top_product = sales_df.groupby('product_id')['quantity_sold'].sum().reset_index()
top_product = top_product.merge(product_df[['product_id', 'product_name']], on='product_id', how='left')
top_product = top_product.sort_values(by='quantity_sold', ascending=False).head(1)

# Most Profitable Category
product_df_with_profit = product_df.merge(
    sales_merged.groupby('product_id')['profit'].sum().reset_index(),
    on='product_id', how='left'
)
category_profit = product_df_with_profit.groupby('category')['profit'].sum().reset_index().sort_values(by='profit', ascending=False).head(1)

# Ensure sales_date is datetime for recent/past filtering
sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'], errors='coerce')

h1, h2, h3 = st.columns(3)

with h1:
    if not top_product.empty:
        st.success(f"🔥 Best-Selling Product: **{top_product.iloc[0]['product_name']}** ({int(top_product.iloc[0]['quantity_sold'])} sold)")
with h2:
    if not category_profit.empty:
        st.info(f"📊 Top Category: **{category_profit.iloc[0]['category']}** (₹ {category_profit.iloc[0]['profit']:,.0f})")
with h3:
    recent_sales = sales_df[sales_df['sales_date'] > pd.Timestamp.now() - pd.Timedelta(days=7)]
    past_sales = sales_df[sales_df['sales_date'] <= pd.Timestamp.now() - pd.Timedelta(days=7)]
    change = recent_sales['quantity_sold'].sum() - past_sales['quantity_sold'].sum()
    trend_icon = "📈" if change >= 0 else "📉"
    st.warning(f"{trend_icon} Sales Trend: {'↑' if change >= 0 else '↓'} {abs(change)} vs last 7 days")

# ----------------------
# Low Stock Alerts
# ----------------------
st.markdown("---")
st.markdown("### ⚠️ Low Stock Alerts")
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
st.markdown("### 📅 Monthly Sales Overview")

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
              title="Monthly Sales Overview",
              markers=True, template='plotly_dark')
fig.update_layout(
    legend_title_text='Metric',
    xaxis_title="Month",
    yaxis_title="Amount",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)
st.plotly_chart(fig, use_container_width=True)

# ----------------------
# Category-wise Breakdown
# ----------------------
st.markdown("---")
st.markdown("### 🧠 Visual Insights")

category_sales = product_df.merge(sales_df.groupby('product_id')['quantity_sold'].sum().reset_index(), on='product_id')
category_grouped = category_sales.groupby('category')['quantity_sold'].sum().reset_index()
category_fig = px.bar(category_grouped, x='category', y='quantity_sold', title="Category-wise Sales", color='quantity_sold', template='plotly_dark')
st.plotly_chart(category_fig, use_container_width=True)
