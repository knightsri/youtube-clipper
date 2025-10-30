#!/bin/bash
# Simple restart with volume mounts

echo "🔄 Restarting YouTube Clipper with volume mounts..."
echo ""

echo "Stopping..."
docker-compose down

echo ""
echo "Starting (rebuilding if needed)..."
docker-compose up -d --build

echo ""
echo "Waiting for startup..."
sleep 2

echo ""
echo "Testing..."
curl -s -I http://localhost:5000 | head -5

echo ""
echo "✅ Done! Access at: http://localhost:5000"
echo ""
echo "📝 Note: Changes to app.py or templates/ will take effect on next request!"