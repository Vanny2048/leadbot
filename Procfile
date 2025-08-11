web: uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
streamlit: streamlit run app/streamlit_app.py --server.port ${STREAMLIT_PORT:-8501} --server.address 0.0.0.0