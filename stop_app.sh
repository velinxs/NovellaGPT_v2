#!/bin/bash

# Check if PID file exists
if [ ! -f streamlit_app.pid ]; then
    echo "No running app found (PID file missing)"
    exit 1
fi

# Read the PID
PID=$(cat streamlit_app.pid)

# Check if process is running
if ps -p $PID > /dev/null; then
    echo "Stopping Streamlit app (PID: $PID)..."
    kill $PID
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $PID > /dev/null; then
        echo "Process still running, forcing termination..."
        kill -9 $PID
    fi
    
    echo "Streamlit app stopped"
else
    echo "No running app found with PID: $PID"
fi

# Remove PID file
rm -f streamlit_app.pid