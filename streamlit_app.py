import io
from typing import List

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simple Streamlit App",
    page_icon="✅",
    layout="wide",
)

st.title("Simple Streamlit App")
st.write("Upload a CSV to preview data and quick stats. That's it.")

with st.sidebar:
    st.header("Options")
    show_describe = st.checkbox("Show describe()", value=True)
    show_line_chart = st.checkbox("Show quick line chart", value=False)

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])  # Keep dependencies minimal

if uploaded_file is None:
    st.info("Awaiting a CSV file upload…")
    st.stop()

try:
    # Rely on pandas' sniffer; utf-8 is typical; adjust if needed
    data = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

if data.empty:
    st.warning("The uploaded CSV appears to be empty.")
    st.stop()

st.subheader("Preview")
st.dataframe(data.head(100), use_container_width=True)

st.caption(f"Rows: {len(data):,} | Columns: {len(data.columns):,}")

if show_describe:
    numeric_cols: List[str] = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
    if numeric_cols:
        st.subheader("Quick stats")
        st.dataframe(data[numeric_cols].describe().T, use_container_width=True)
    else:
        st.info("No numeric columns found for stats.")

if show_line_chart:
    numeric_cols: List[str] = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
    if numeric_cols:
        st.subheader("Quick line chart")
        st.line_chart(data[numeric_cols].iloc[:200])
    else:
        st.info("No numeric columns available for line chart.")

st.success("Ready. Upload a different CSV anytime from the uploader above.")