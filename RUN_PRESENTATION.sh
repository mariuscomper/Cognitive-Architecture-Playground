#!/bin/bash

echo ""
echo "🎓 Starting Stoicism Presentation Server..."
echo "=========================================="
echo ""

# Check if server is already running
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✓ Server is already running!"
    echo ""
    echo "Open in browser: http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop this message."
    echo "To stop the server, kill the process on port 8000"
    echo ""
else
    echo "Starting new server..."
    python3 server.py
fi
