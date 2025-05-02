#!/bin/bash

# Set working directory
cd /home/velinxs/Documents/Coding/Misc/NovellaGPT_v2/

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOF
anthropic>=0.50.0
openai>=1.76.0
streamlit>=1.44.0
pydub>=0.25.1
fpdf>=1.7.2
python-dotenv>=1.1.0
tiktoken>=0.9.0
EOF
fi

# Install requirements if needed
pip install -r requirements.txt

# Create directory for audio files if it doesn't exist
mkdir -p audio_files

# Start app
echo "Starting NovellaGPT v2 with audiobook functionality..."
streamlit run novella_app.py