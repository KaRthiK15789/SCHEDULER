#!/bin/bash

# Get the port from environment or default to 5000
PORT=${PORT:-5000}

# Start the FastAPI backend in the background on port 8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 10

# Start Streamlit frontend on the main port
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
