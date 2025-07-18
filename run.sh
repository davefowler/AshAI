#!/bin/bash
echo "Starting server at http://localhost:8000"
uvicorn main:app --reload 