import streamlit as st

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Retail Inventory Management",
    page_icon="📦",
    layout="wide"
)

# Main page content
st.title("📦 Welcome to the Retail Inventory Management System")
st.markdown("""
This is a data-driven platform to help retailers make smarter decisions by managing:

- 📋 Inventory: Track stock levels, product variations, and category details.
- 📈 Sales: Analyze product performance, revenue trends, and order statuses.
- 📥 Purchases: Monitor vendor performance, track payment dues, and manage order pipelines.

### 🔁 How to Get Started:
1. Head to the **Upload or Add Data** page to upload your inventory, sales, and purchase data.
2. Navigate through the sidebar to view **real-time dashboards** and **deep insights**.
3. Monitor stock alerts, sales trends, and vendor activity in one unified interface.

---

✅ Built with **Streamlit**, **MySQL**, and **Python**  
🌐 Designed for modern retail operations.
""")

st.image("https://cdn.zoho.com/sites/default/files/styles/product-overview/public/2022-06/inventory-management.svg", width=700)
