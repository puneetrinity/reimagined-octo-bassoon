#!/bin/bash
# Quick restart script for the FastAPI application service
# Use this to restart just the app service when changing configuration

echo "🔄 Restarting AI Search App service..."

# Stop the app service
supervisorctl stop ai-search-app

# Wait a moment
sleep 2

# Start the app service
supervisorctl start ai-search-app

# Check status
echo "📊 Service status:"
supervisorctl status ai-search-app

echo "✅ App service restart complete!"
echo "🌐 API should now accept CORS requests from your frontend domain"
