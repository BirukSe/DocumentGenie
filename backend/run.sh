#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
