#!/bin/bash

# This script is used to test if the DeepSeek-R1 8B model is available and pull it if not

echo "🔍 Checking for DeepSeek-R1 8B model..."

if ! ollama list | grep -q "deepseek-r1:8b"; then
  echo "⬇️ DeepSeek-R1 8B model not found. Pulling from Ollama library..."
  ollama pull deepseek-r1:8b
  echo "✅ DeepSeek-R1 8B model has been installed."
else
  echo "✅ DeepSeek-R1 8B model is already installed."
fi

# Test the model with a simple prompt
echo "🧪 Testing the model..."
echo '{"model": "deepseek-r1:8b", "prompt": "Write a short greeting", "stream": false}' | \
  curl -s -X POST http://localhost:11434/api/generate -d @- | \
  jq -r '.response'

echo "✅ Model test completed!"
