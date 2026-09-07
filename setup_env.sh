#!/bin/zsh
# Setup script for Facial Emotion Recognition environment
# Usage: source ./setup_env.sh OR ./setup_env.sh

# Create a virtual environment if not present
echo "Creating Python virtual environment in .venv..."
python3 -m venv .venv

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

echo "Environment setup complete. To activate later, run: source .venv/bin/activate"
