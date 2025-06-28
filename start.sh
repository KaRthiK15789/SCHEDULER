#!/bin/bash

# Go into SCHEDULER directory
cd SCHEDULER

# Make sure Python can find backend
export PYTHONPATH=.

# Start FastAPI backend
python -m backend.main --host 0.0.0.0 --port 8000 &

# Wait for backend to boot
sleep 10

# Start Streamlit app
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
