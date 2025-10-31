#!/bin/bash

# YouTube Clipper v2.0 - Quick Start Script

echo "========================================"
echo "YouTube Video Clipper v2.0"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create data directory if it doesn't exist
mkdir -p data

echo "Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Check the error messages above."
    exit 1
fi

echo ""
echo "✓ Build successful!"
echo ""

echo "Starting YouTube Clipper..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start the application. Check the error messages above."
    exit 1
fi

echo ""
echo "========================================"
echo "✓ YouTube Clipper is now running!"
echo "========================================"
echo ""
echo "Access the application:"
echo "  • Local:   http://localhost:5000"
echo "  • Network: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Useful commands:"
echo "  • View logs:    docker-compose logs -f"
echo "  • Stop app:     docker-compose down"
echo "  • Restart app:  docker-compose restart"
echo ""
echo "For help, see docs/README.md"
echo "========================================"
