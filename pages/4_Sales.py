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
    purchases = pd.read_sql("SELECT product_id, cost_price FROM purchases", conn)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# -------------------------
# DEBUG: Show raw data
# -------------------------
st.sidebar.checkbox("Show Raw Data", key="debug")

if st.session_state.debug:
    st.subheader("🔍 Raw Sales Data")
    st.write(sales)
    st.write("Products Table", products)
    st.write("Purchases Table", purchases)

# -------------------------
# Merge product and cost info
# -------------------------
sales = sales.merge(products, on='product_id', how='left')
sales = sales.merge(purchases, on='product_id', how='left')

# Check for missing merges
if sales['product_name'].isnull().all():
    st.warning("⚠️ No matching product_id found in `product` table. Check data consistency.")
if sales['cost_price'].isnull().all():
    st.warning("⚠️ No matching product_id found in `purchases` table for cost_price.")

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
# Display Sales Data
# -------------------------
st.subheader("📋 Sales Transactions")

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
st.subheader("🏆 Top-Selling Products")

top_products = filtered_sales.groupby('product_name').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'profit': 'sum'
}).sort_values(by='quantity_sold', ascending=False).reset_index().head(10)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(top_products, x='product_name', y='quantity_sold', title="Top 10 Products by Quantity")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(top_products, x='product_name', y='revenue', title="Top 10 Products by Revenue")
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# Monthly Trend Charts
# -------------------------
st.markdown("---")
st.subheader("📆 Monthly Sales Performance")

sales_monthly = filtered_sales.copy()
sales_monthly['month'] = sales_monthly['sales_date'].dt.to_period('M').astype(str)
monthly_grouped = sales_monthly.groupby('month')[['quantity_sold', 'revenue', 'profit']].sum().reset_index()

tab1, tab2, tab3 = st.tabs(["📦 Quantity", "💰 Revenue", "📈 Profit"])

with tab1:
    fig3 = px.line(monthly_grouped, x='month', y='quantity_sold', title="Monthly Units Sold")
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    fig4 = px.line(monthly_grouped, x='month', y='revenue', title="Monthly Revenue")
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    fig5 = px.line(monthly_grouped, x='month', y='profit', title="Monthly Profit")
    st.plotly_chart(fig5, use_container_width=True)
