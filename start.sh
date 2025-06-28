#!/bin/bash

# Get the port from environment or default to 5000
PORT=${PORT:-5000}

cd scheduler

# Set PYTHONPATH so backend is findable
export PYTHONPATH=.

# Start FastAPI backend
python -m backend.main --host 0.0.0.0 --port 8000 &

# Wait for backend to boot up
sleep 10

# Start Streamlit
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
