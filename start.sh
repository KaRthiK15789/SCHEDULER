#!/bin/bash

PORT=${PORT:-5000}
export PYTHONPATH=./SCHEDULER-main

python -m SCHEDULER-main.backend.main --host 0.0.0.0 --port 8000 &
sleep 10
streamlit run SCHEDULER-main/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
