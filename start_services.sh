#!/bin/bash

# Kill any existing processes
echo "Stopping existing services..."
pkill -f "python main_supabase.py" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sleep 2

# Start backend
echo "Starting backend on port 8001..."
cd /root/amazon-helper
source venv/bin/activate
nohup python main_supabase.py > server.log 2>&1 &
echo "Backend PID: $!"

# Start frontend
echo "Starting frontend on port 5173..."
cd /root/amazon-helper/frontend
nohup npm run dev > frontend.log 2>&1 &
echo "Frontend PID: $!"

sleep 3

# Check if services are running
echo ""
echo "Checking services..."
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✓ Backend is running at http://localhost:8001"
else
    echo "✗ Backend failed to start"
fi

if curl -s http://localhost:5173 > /dev/null; then
    echo "✓ Frontend is running at http://localhost:5173"
else
    echo "✗ Frontend failed to start"
fi

echo ""
echo "Access the application at: http://localhost:5173"
echo "Login with: nick@nevermeh.com"