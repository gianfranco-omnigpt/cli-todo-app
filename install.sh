#!/bin/bash
# 
# Installation script for CLI Todo Application
# 
# This script installs the todo application to /usr/local/bin/
# Alternatively, you can install to ~/bin/ by passing --user flag
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/usr/local/bin"
USE_SUDO=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            INSTALL_DIR="$HOME/bin"
            USE_SUDO=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --user    Install to ~/bin instead of /usr/local/bin (no sudo required)"
            echo "  --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Install system-wide (requires sudo)"
            echo "  $0 --user       # Install for current user only"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run '$0 --help' for usage information."
            exit 1
            ;;
    esac
done

echo -e "${GREEN}CLI Todo Application - Installation Script${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.7 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Create installation directory if it doesn't exist (for --user mode)
if [ "$USE_SUDO" = false ]; then
    mkdir -p "$INSTALL_DIR"
    echo -e "${GREEN}✓${NC} Created directory: $INSTALL_DIR"
fi

# Download the script
SCRIPT_NAME="todo"
SCRIPT_URL="https://raw.githubusercontent.com/gianfranco-omnigpt/cli-todo-app/main/todo.py"

echo ""
echo "Downloading todo application..."

if command -v curl &> /dev/null; then
    curl -fsSL "$SCRIPT_URL" -o "/tmp/$SCRIPT_NAME"
elif command -v wget &> /dev/null; then
    wget -q "$SCRIPT_URL" -O "/tmp/$SCRIPT_NAME"
else
    echo -e "${RED}Error: Neither curl nor wget is installed.${NC}"
    echo "Please install curl or wget and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Downloaded successfully"

# Make the script executable
chmod +x "/tmp/$SCRIPT_NAME"

# Install the script
echo ""
echo "Installing to $INSTALL_DIR..."

if [ "$USE_SUDO" = true ]; then
    if sudo mv "/tmp/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"; then
        echo -e "${GREEN}✓${NC} Installed successfully to $INSTALL_DIR/$SCRIPT_NAME"
    else
        echo -e "${RED}Error: Failed to install. Do you have sudo privileges?${NC}"
        echo "Try running with --user flag: $0 --user"
        exit 1
    fi
else
    if mv "/tmp/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"; then
        echo -e "${GREEN}✓${NC} Installed successfully to $INSTALL_DIR/$SCRIPT_NAME"
    else
        echo -e "${RED}Error: Failed to install to $INSTALL_DIR${NC}"
        exit 1
    fi
fi

# Check if the installation directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH.${NC}"
    echo ""
    echo "To use the 'todo' command, add this line to your shell config file:"
    echo ""
    
    if [ -f "$HOME/.bashrc" ]; then
        echo "    echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
        echo "    source ~/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        echo "    echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
        echo "    source ~/.zshrc"
    else
        echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
    fi
    echo ""
fi

# Test the installation
echo ""
echo "Testing installation..."
if command -v todo &> /dev/null; then
    echo -e "${GREEN}✓${NC} Installation successful!"
    echo ""
    echo -e "${GREEN}The 'todo' command is now available!${NC}"
else
    # If not in path, try direct execution
    if [ -x "$INSTALL_DIR/$SCRIPT_NAME" ]; then
        echo -e "${GREEN}✓${NC} Installation successful!"
        echo ""
        echo -e "${YELLOW}Note: Run 'todo' using the full path:${NC}"
        echo "    $INSTALL_DIR/todo"
    else
        echo -e "${RED}Installation may have failed. Please check the error messages above.${NC}"
        exit 1
    fi
fi

echo ""
echo "Quick start:"
echo "  todo add \"My first task\"    # Add a task"
echo "  todo list                    # List tasks"
echo "  todo complete <id>           # Complete a task"
echo "  todo delete <id>             # Delete a task"
echo "  todo --help                  # Show help"
echo ""
echo "Tasks are stored in: ~/.todo/tasks.json"
echo ""
echo -e "${GREEN}Happy organizing! 🎉${NC}"