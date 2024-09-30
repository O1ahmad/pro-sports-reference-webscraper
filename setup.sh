#!/bin/bash

# Enable strict mode to catch errors early
set -euo pipefail

# Variables
REPO_URL="git@github.com:O1ahmad/pro-sports-reference-webscraper.git"
PROJECT_DIR="pro-sports-reference-webscraper"
VENV_DIR="venv"

# Function to handle errors
handle_error() {
    echo "Error occurred at line $1"
    exit 1
}
trap 'handle_error $LINENO' ERR

# Step 1: Update package lists
echo "Updating package lists..."
sudo apt update -y

# Step 2: Install python3-pip if not installed
echo "Installing python3-pip..."
if ! dpkg -s python3-pip >/dev/null 2>&1; then
    sudo apt install python3-pip -y
else
    echo "python3-pip is already installed."
fi

# Step 3: Install python3-virtualenv if not installed
echo "Installing python3-virtualenv..."
if ! dpkg -s python3-virtualenv >/dev/null 2>&1; then
    sudo apt install python3-virtualenv -y
else
    echo "python3-virtualenv is already installed."
fi

# Step 4: Ensure SSH doesn't prompt for confirmation of new hosts
# Add the GitHub server to known hosts to avoid the SSH prompt
echo "Adding GitHub to known hosts to avoid SSH prompt..."
ssh-keyscan -H github.com >> ~/.ssh/known_hosts

# Step 5: Clone the repository if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Cloning repository..."
    GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" git clone "$REPO_URL"
else
    echo "Repository already cloned."
fi

# Step 6: Change into the project directory
echo "Navigating to project directory..."
cd "$PROJECT_DIR"

# Step 7: Set up the virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    virtualenv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# Step 8: Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 9: Install required Python packages
if [ -f "requirements.txt" ]; then
    echo "Installing required Python packages..."
    pip3 install -r requirements.txt
else
    echo "requirements.txt not found. Skipping package installation."
fi

echo "Setup completed successfully!"

