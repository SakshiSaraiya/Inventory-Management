import streamlit as st
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# ✅ mysql.connector — for transactional operations (used by upload_data.py)
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"]
    )

# ✅ SQLAlchemy + pymysql — for analytics (used by pandas.read_sql)
@st.cache_resource
def get_engine():
    return create_engine(
        f"mysql+pymysql://{st.secrets['mysql']['user']}:{st.secrets['mysql']['password']}@"
        f"{st.secrets['mysql']['host']}:{st.secrets['mysql']['port']}/{st.secrets['mysql']['database']}"
    )

def fetch_query(query):
    engine = get_engine()
    return pd.read_sql(query, engine)
