import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title="🏬 Home", layout="wide")
st.title("📊 Retail Dashboard")

# -------------------------
# Connect to DB
# -------------------------
conn = get_connection()
product_df = pd.read_sql("SELECT * FROM product", conn)
sales_df = pd.read_sql("SELECT product_id, quantity_sold, selling_price, sales_date FROM sales", conn)
purchase_df = pd.read_sql("SELECT product_id, quantity_purchased FROM purchases", conn)

# -------------------------
# Aggregate sales & purchase
# -------------------------
total_products = product_df.shape[0]
total_stock = purchase_df['quantity_purchased'].sum()
total_sold = sales_df['quantity_sold'].sum()
total_revenue = (sales_df['quantity_sold'] * sales_df['selling_price']).sum()

# Merge sales with purchases to calculate profit
sales_merge = sales_df.merge(product_df[['product_id']], on='product_id', how='left')
cost_df = pd.read_sql("SELECT product_id, cost_price FROM purchases", conn)
sales_merge = sales_merge.merge(cost_df.groupby('product_id').mean().reset_index(), on='product_id', how='left')
sales_merge['profit'] = sales_merge['quantity_sold'] * (sales_merge['selling_price'] - sales_merge['cost_price'])
total_profit = sales_merge['profit'].sum()

# -------------------------
# KPI Cards with Icons
# -------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("📦 Total Products", total_products)
kpi2.metric("📥 Total Stock", total_stock)
kpi3.metric("📤 Total Units Sold", total_sold)
kpi4.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
kpi5.metric("📈 Total Profit", f"₹ {total_profit:,.2f}")

style_metric_cards(border_left_color="#FF4B4B")

# -------------------------
# Low Stock Alert
# -------------------------
st.markdown("---")
st.subheader("🚨 Low Stock Alerts")
threshold = st.slider("Set stock threshold", 1, 50, 10)

# Inventory check
inventory_df = product_df.merge(purchase_df.groupby('product_id').sum(), on='product_id', how='left')
inventory_df = inventory_df.merge(sales_df.groupby('product_id').sum(), on='product_id', how='left')
inventory_df.fillna(0, inplace=True)
inventory_df['live_stock'] = inventory_df['quantity_purchased'] - inventory_df['quantity_sold']

low_stock_df = inventory_df[inventory_df['live_stock'] < threshold]

if low_stock_df.empty:
    st.success("✅ All products have sufficient stock.")
else:
    st.error(f"⚠️ {low_stock_df.shape[0]} products are low on stock.")
    st.dataframe(low_stock_df[['product_id', 'product_name', 'live_stock']])

# -------------------------
# Monthly Trend Chart
# -------------------------
st.markdown("---")
st.subheader("📆 Monthly Sales Trend")

try:
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
except KeyError as e:
    st.warning(f"⚠️ Monthly sales trend cannot be displayed: missing column {e}")
