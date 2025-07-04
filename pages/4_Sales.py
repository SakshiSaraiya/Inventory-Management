import streamlit as st 
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📈 Sales", layout="wide")
st.title("📈 Sales Overview")

# -------------------------
# Connect to MySQL
# -------------------------
conn = get_connection()

# -------------------------
# Load raw tables
# -------------------------
try:
    sales = pd.read_sql("SELECT * FROM sales", conn)
    products = pd.read_sql("SELECT * FROM product", conn)
    purchases = pd.read_sql("SELECT product_id, product_name AS product_name_purchases, cost_price FROM purchases", conn)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# -------------------------
# Normalize product_id across all tables
# -------------------------
sales['product_id'] = sales['product_id'].astype(str).str.strip().str.upper()
products['product_id'] = products['product_id'].astype(str).str.strip().str.upper()
purchases['product_id'] = purchases['product_id'].astype(str).str.strip().str.upper()

# -------------------------
# Merge product info from product and purchases
# -------------------------
sales = sales.merge(products, on='product_id', how='left')
sales = sales.merge(purchases, on='product_id', how='left')

# Fallback logic for product_name and cost_price
sales['product_name'] = sales['product_name'].fillna(sales['product_name_purchases'])

# -------------------------
# DEBUG: Show raw data
# -------------------------
if st.sidebar.checkbox("Show Raw Data", key="debug"):
    st.subheader("🔍 Raw Sales Data")
    st.write("Sales Table", sales)
    st.write("Products Table", products)
    st.write("Purchases Table", purchases)

# -------------------------
# Check for missing merges
# -------------------------
if sales['product_name'].isnull().all():
    st.warning("⚠️ No matching product_id found in product or purchases table.")
if sales['cost_price'].isnull().all():
    st.warning("⚠️ No matching cost_price found in purchases table.")

# -------------------------
# Parse sales_date column
# -------------------------
try:
    sales['sales_date'] = pd.to_datetime(sales['sales_date'], errors='coerce')
except Exception as e:
    st.warning(f"⚠️ Couldn't parse sales_date column: {e}")

# -------------------------
# Calculate revenue and profit
# -------------------------
sales['revenue'] = sales['quantity_sold'] * sales['selling_price']
sales['profit'] = sales['quantity_sold'] * (sales['selling_price'] - sales['cost_price'])

# -------------------------
# Filter Section
# -------------------------
st.sidebar.header("🔍 Filter Sales")

all_products = sales['product_name'].dropna().unique()
product_filter = st.sidebar.multiselect("Product Name", all_products, default=list(all_products))

shipped_filter = st.sidebar.selectbox("Shipped Status", ["All"] + sales['shipped_status'].dropna().unique().tolist())
payment_filter = st.sidebar.selectbox("Payment Status", ["All"] + sales['payment_status'].dropna().unique().tolist())

start_date = st.sidebar.date_input("Start Date", value=sales['sales_date'].min())
end_date = st.sidebar.date_input("End Date", value=sales['sales_date'].max())

# -------------------------
# Apply Filters
# -------------------------
filtered_sales = sales[
    (sales['product_name'].isin(product_filter)) &
    (sales['sales_date'] >= pd.to_datetime(start_date)) &
    (sales['sales_date'] <= pd.to_datetime(end_date))
]

if shipped_filter != "All":
    filtered_sales = filtered_sales[filtered_sales['shipped_status'] == shipped_filter]

if payment_filter != "All":
    filtered_sales = filtered_sales[filtered_sales['payment_status'] == payment_filter]

# -------------------------
# KPI Metrics
# -------------------------
st.markdown("### 📊 Sales KPIs")
k1, k2, k3, k4 = st.columns(4)
k1.metric("🧾 Total Sales", int(filtered_sales['quantity_sold'].sum()))
k2.metric("💰 Total Revenue", f"₹ {filtered_sales['revenue'].sum():,.2f}")
k3.metric("📈 Total Profit", f"₹ {filtered_sales['profit'].sum():,.2f}")
k4.metric("🛍️ Orders", len(filtered_sales))

# -------------------------
# Display Sales Data
# -------------------------
st.markdown("### 📋 Sales Transactions")

if filtered_sales.empty:
    st.warning("⚠️ No matching sales records found with current filters.")
else:
    st.dataframe(
        filtered_sales[['sale_id', 'sales_date', 'product_name', 'quantity_sold', 'revenue', 'profit', 'shipped_status', 'payment_status']],
        use_container_width=True
    )

# -------------------------
# Top Products Section
# -------------------------
st.markdown("---")
st.markdown("### 🏆 Top-Selling Products")

top_n = st.slider("Top N Products", 5, 20, 10)
top_products = filtered_sales.groupby('product_name').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'profit': 'sum'
}).sort_values(by='quantity_sold', ascending=False).reset_index().head(top_n)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        top_products,
        x='product_name',
        y='quantity_sold',
        title=f"Top {top_n} Products by Quantity",
        color='quantity_sold',
        template='plotly_dark',
        animation_frame=None
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(
        top_products,
        x='product_name',
        y='revenue',
        title=f"Top {top_n} Products by Revenue",
        color='revenue',
        template='plotly_dark',
        animation_frame=None
    )
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# Monthly Trend Charts
# -------------------------
st.markdown("---")
st.markdown("### 📆 Monthly Sales Performance")

sales_monthly = filtered_sales.copy()
sales_monthly['month'] = sales_monthly['sales_date'].dt.to_period('M').astype(str)
monthly_grouped = sales_monthly.groupby('month')[['quantity_sold', 'revenue', 'profit']].sum().reset_index()

tab1, tab2, tab3 = st.tabs(["📦 Quantity", "💰 Revenue", "📈 Profit"])

with tab1:
    fig3 = px.line(
        monthly_grouped,
        x='month',
        y='quantity_sold',
        title="Monthly Units Sold",
        markers=True,
        template='plotly_dark',
        animation_frame=None
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    fig4 = px.line(
        monthly_grouped,
        x='month',
        y='revenue',
        title="Monthly Revenue",
        markers=True,
        template='plotly_dark',
        animation_frame=None
    )
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    fig5 = px.line(
        monthly_grouped,
        x='month',
        y='profit',
        title="Monthly Profit",
        markers=True,
        template='plotly_dark',
        animation_frame=None
    )
    st.plotly_chart(fig5, use_container_width=True)
