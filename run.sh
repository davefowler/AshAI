#!/bin/bash
echo "Starting server at http://localhost:8000"
source venv/bin/activate
./venv/bin/uvicorn main:app --reload 