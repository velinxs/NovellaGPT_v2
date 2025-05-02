#!/bin/bash

# Get the full path to the virtual environment activate script
VENV_ACTIVATE="$(pwd)/venv/bin/activate"

# Log file location
LOG_FILE="$(pwd)/streamlit_app.log"

# Create a script that will be executed in the background
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << EOF
#!/bin/bash
source "$VENV_ACTIVATE"
cd "$(pwd)"
streamlit run novella_app.py --server.headless=true > "$LOG_FILE" 2>&1
EOF

chmod +x "$TMP_SCRIPT"

# Run the script in the background, detached from the terminal
nohup bash "$TMP_SCRIPT" &

# Store the process ID so it can be killed later if needed
PID=$!
echo $PID > streamlit_app.pid

echo "Streamlit app started in the background with PID: $PID"
echo "View logs at: $LOG_FILE"
echo "Access the app at: http://localhost:8501"
echo ""
echo "To stop the app, run: ./stop_app.sh"