#!/bin/bash
# Start Streamlit in the background
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &

# Start API from main.py using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000