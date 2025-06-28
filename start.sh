#!/bin/bash

# Get the port from Render environment or default to 5000
PORT=${PORT:-5000}

# Set Python path so backend can be imported
export PYTHONPATH=.

# Start FastAPI backend in the background on port 8000
python -m backend.main --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 10

# Start Streamlit app on main Render port
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
