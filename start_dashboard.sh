#!/bin/bash
echo "Starting Synthetic Data Quality Dashboard..."

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo "Starting FastAPI Backend on port 8000..."
uvicorn src.synthetic_generator.api:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting Vite Frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "=================================================="
echo "Dashboard is running! Access the UI at http://localhost:5173"
echo "API Backend is running at http://localhost:8000"
echo "Press Ctrl+C to stop both servers."
echo "=================================================="

# Trap Ctrl+C (SIGINT) to kill both processes
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
