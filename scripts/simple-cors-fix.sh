#!/bin/bash
# Simple environment variable CORS fix
# This sets the environment variable and restarts the service

echo "🔧 Setting CORS environment variable..."

# Set the environment variable for the current session
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000,https://feb7cb5f-ab08-463c-86a3-8fc7230da68e-00-3ruaw352aa5oh.kirk.replit.dev"

# Add to system environment (persistent)
echo "export ALLOWED_ORIGINS=\"$ALLOWED_ORIGINS\"" >> /root/.bashrc

# Restart the FastAPI service to pick up the new environment variable
echo "🔄 Restarting FastAPI service..."
supervisorctl restart ai-search-app

# Wait and check status
sleep 3
supervisorctl status ai-search-app

echo "✅ CORS fix applied via environment variable!"
echo "🌐 Allowed origins: $ALLOWED_ORIGINS"
