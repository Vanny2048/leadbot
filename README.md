# Streamlit App

A minimal Streamlit app that previews CSV files and shows quick stats.

## Quick start (recommended)

```bash
pip install -r requirements.txt
python3 -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

- Open the app at: http://localhost:8501
- Upload a CSV to see a preview, optional `describe()` stats, and a quick line chart.
- Stop the app with Ctrl+C in the terminal.

## If `streamlit` command is not found

Use the module form which avoids PATH issues:

```bash
python3 -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

If you installed with `--user` and want to use the `streamlit` binary directly, ensure your PATH includes the user bin directory:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Optional: use a virtual environment (if supported on your system)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

## Features
- Upload any `.csv`
- Preview first 100 rows
- Optional `describe()` for numeric columns
- Optional quick line chart for numeric columns