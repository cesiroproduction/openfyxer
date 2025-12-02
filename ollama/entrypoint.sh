#!/bin/bash
set -e

echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 10

# Check if tinyllama model exists, if not download it
echo "Checking for tinyllama model..."
if ! ollama list | grep -q "tinyllama"; then
    echo "Downloading tinyllama model (this may take a few minutes on first run)..."
    ollama pull tinyllama
    echo "tinyllama model downloaded successfully!"
else
    echo "tinyllama model already available."
fi

echo "Ollama is ready with tinyllama model!"

# Keep the container running
wait
