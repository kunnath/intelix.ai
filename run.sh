#!/bin/bash

# Check if Ollama is running
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags | grep -q "200"; then
  echo "❌ Ollama is not running! Please start Ollama first."
  echo "   You can start it with: 'ollama serve'"
  exit 1
fi

# Check if DeepSeek model is available
if ! curl -s http://localhost:11434/api/tags | grep -q "deepseek-r1:8b"; then
  echo "❌ DeepSeek-R1 8B model not found! Installing..."
  ollama pull deepseek-r1:8b
fi

echo "✅ Ollama is running with DeepSeek-R1 8B model"
echo "🚀 Starting IntelliX.AI Test Case Generator..."
echo "📊 Qdrant UI will be available at: http://localhost:6333/dashboard"

docker-compose up --build
