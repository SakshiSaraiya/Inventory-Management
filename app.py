import streamlit as st
from streamlit_lottie import st_lottie
import requests

# --- Load Lottie Animation ---
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

inventory_lottie = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")

# Set page configuration
st.set_page_config(
    page_title="Retail Inventory Management",
    page_icon="📦",
    layout="wide"
)

# --- Title and Description ---
st.markdown("<h1 style='text-align:center;'>📦 Retail Inventory Management System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:18px;'>Empowering retailers with real-time insights and control.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Layout Columns ---
left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("🔧 Features:")
    st.markdown("""
    - 📋 **Inventory**: Track stock levels, product variations, and categories.
    - 📈 **Sales**: View product performance, trends, and orders.
    - 📅 **Purchases**: Manage vendor performance and payment schedules.
    """)

    st.subheader(":rocket: Get Started:")
    st.markdown("""
    1. Go to the **Upload or Add Data** page.
    2. Explore dashboards through the **sidebar**.
    3. Monitor trends, alerts, and inventory health — all in one place!
    """)

    st.subheader(":gear: Built With:")
    st.markdown("""
    - 🧰 Python + Streamlit  
    - 📁 MySQL  
    - 📊 Realtime Dashboards
    """)

    st.subheader(":compass: Quick Navigation:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Upload Data"):
            st.switch_page("pages/0_upload_data.py")
    with col2:
        if st.button("📊 View Inventory"):
            st.switch_page("pages/1_Home.py")

with right_col:
    st_lottie(inventory_lottie, height=300, key="inventory_anim")
    st.image("assets/theme-image.png", caption="Smart inventory, smart business.", use_column_width=True)

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align:center;'>🔒 Secure | ⚡ Fast | 🌟 Accurate</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; font-size:12px;'>Built with ❤️ by Sakshi Saraiya & Chirag Thakkar</div>", unsafe_allow_html=True)
