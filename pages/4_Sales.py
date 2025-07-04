import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_connection

st.set_page_config(page_title="📈 Sales", layout="wide")
st.title("📈 Sales Overview")

# Connect to MySQL
conn = get_connection()

# Load sales and product data
sales = pd.read_sql("SELECT * FROM Sales", conn)
products = pd.read_sql("SELECT * FROM Products", conn)

# Merge data
sales = sales.merge(products, on='product_id', how='left')
sales['sale_date'] = pd.to_datetime(sales['sale_date'])
sales['revenue'] = sales['quantity_sold'] * sales['selling_price']
sales['profit'] = sales['quantity_sold'] * (sales['selling_price'] - sales['cost_price'])

# -------------------------
# Filters
# -------------------------
st.sidebar.header("🔍 Filter Sales")

all_products = sales['name'].dropna().unique()
product_filter = st.sidebar.multiselect("Product Name", all_products, default=list(all_products))

shipped_filter = st.sidebar.selectbox("Shipped Status", ["All", "Shipped", "Unshipped"])
payment_filter = st.sidebar.selectbox("Payment Status", ["All", "Received", "Pending"])

start_date = st.sidebar.date_input("Start Date", value=sales['sale_date'].min())
end_date = st.sidebar.date_input("End Date", value=sales['sale_date'].max())

# Apply Filters
filtered_sales = sales[
    (sales['name'].isin(product_filter)) &
    (sales['sale_date'] >= pd.to_datetime(start_date)) &
    (sales['sale_date'] <= pd.to_datetime(end_date))
]

if shipped_filter != "All":
    filtered_sales = filtered_sales[filtered_sales['shipped'] == (shipped_filter == "Shipped")]

if payment_filter != "All":
    filtered_sales = filtered_sales[filtered_sales['payment_received'] == (payment_filter == "Received")]

# -------------------------
# Sales Table
# -------------------------
st.subheader("📋 Sales Transactions")

st.dataframe(
    filtered_sales[['sale_id', 'sale_date', 'name', 'quantity_sold', 'revenue', 'profit', 'shipped', 'payment_received']],
    use_container_width=True
)

# -------------------------
# Top Products
# -------------------------
st.markdown("---")
st.subheader("🏆 Top-Selling Products")

top_products = filtered_sales.groupby('name').agg({
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'profit': 'sum'
}).sort_values(by='quantity_sold', ascending=False).reset_index().head(10)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(top_products, x='name', y='quantity_sold', title="Top 10 Products by Quantity")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(top_products, x='name', y='revenue', title="Top 10 Products by Revenue")
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# Monthly Sales Trend
# -------------------------
st.markdown("---")
st.subheader("📆 Monthly Sales Performance")

sales_monthly = filtered_sales.copy()
sales_monthly['month'] = sales_monthly['sale_date'].dt.to_period('M').astype(str)
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
