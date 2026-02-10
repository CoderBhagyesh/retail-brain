import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RetailBrain", layout="wide")
st.title("🧠 RetailBrain – AI Retail Copilot")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Dashboard", "Copilot", "Forecast"])

if page == "Home":
    st.header("Upload Sales Data")
    file = st.file_uploader("Upload CSV", type=["csv"])
    if file and st.button("Upload"):
        res = requests.post(f"{BACKEND_URL}/upload", files={"file": file})
        st.success(res.json())

elif page == "Dashboard":
    st.header("📊 Dashboard")
    res = requests.get(f"{BACKEND_URL}/dashboard/metrics").json()
    if "error" in res:
        st.error(res["error"])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", res["total_revenue"])
        col2.metric("Top Product", res["top_product"])
        col3.metric("Slow Mover", res["slow_mover"])
        st.write("Low Stock Products:", res["low_stock_products"])

elif page == "Copilot":
    st.header("💬 AI Copilot")
    query = st.text_input("Ask a question")
    if st.button("Ask"):
        res = requests.post(f"{BACKEND_URL}/copilot/chat", params={"query": query}).json()
        st.success(res["answer"])

elif page == "Forecast":
    st.header("🔮 Forecast")
    product = st.text_input("Product name")
    days = st.slider("Days", 7, 30, 7)
    if st.button("Get Forecast"):
        res = requests.get(f"{BACKEND_URL}/forecast", params={"product": product, "days": days}).json()
        st.write(res)
