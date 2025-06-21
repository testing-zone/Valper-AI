#!/bin/bash

# Valper AI Assistant - Frontend Start Script

set -e

echo "🚀 Starting Valper AI Assistant Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+ first"
    exit 1
fi

# Check if we're in the frontend directory or root
if [ -f "package.json" ]; then
    echo "Starting from frontend directory..."
elif [ -d "frontend" ]; then
    echo "Starting from root directory..."
    cd frontend
else
    echo "❌ Frontend directory not found"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start the development server
echo "Starting React development server..."
npm start

echo "🎉 Frontend started on http://localhost:3000" 