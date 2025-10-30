#!/bin/bash
# Automated build and start script for YouTube Clipper

set -e  # Exit on any error

echo "🎵 YouTube Dance Clip Extractor - Setup"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the youtube-clipper directory"
    exit 1
fi

echo "✅ In correct directory"
echo ""

# Verify required files
echo "Verifying required files..."
MISSING_FILES=()

[ ! -f "Dockerfile" ] && MISSING_FILES+=("Dockerfile")
[ ! -f "app.py" ] && MISSING_FILES+=("app.py")
[ ! -f "requirements.txt" ] && MISSING_FILES+=("requirements.txt")
[ ! -d "templates" ] && MISSING_FILES+=("templates/")
[ ! -f "templates/index.html" ] && MISSING_FILES+=("templates/index.html")

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files present"
echo ""

# Check for existing containers
if docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Existing container found${NC}"
    read -p "Stop and rebuild? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing containers..."
        docker-compose down
    else
        echo "Keeping existing containers. Exiting."
        exit 0
    fi
fi

# Build
echo ""
echo "Building Docker image..."
echo "This may take 2-3 minutes on first build..."
echo ""

if docker-compose build; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check TROUBLESHOOTING.md"
    echo "2. Try: docker-compose build --no-cache"
    echo "3. Check: docker-compose logs"
    exit 1
fi

# Start
echo ""
echo "Starting container..."
docker-compose up -d

# Wait a moment for startup
sleep 2

# Check if running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo -e "${GREEN}✅ SUCCESS! Application is running${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📱 Access the application:"
    echo ""
    echo "   Local:    http://localhost:5000"
    echo ""
    
    # Try to detect local IP
    if command -v hostname &> /dev/null; then
        LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
        if [ ! -z "$LOCAL_IP" ]; then
            echo "   Network:  http://$LOCAL_IP:5000"
            echo ""
        fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎓 Next steps:"
    echo "1. Open the URL above in your browser"
    echo "2. Paste a YouTube URL and time range"
    echo "3. Click 'Extract Clips'"
    echo ""
    echo "📚 For help, see:"
    echo "   - QUICKSTART.md (quick guide)"
    echo "   - README.md (full docs)"
    echo "   - TROUBLESHOOTING.md (if issues)"
    echo ""
    echo "🛠️  Useful commands:"
    echo "   View logs:   docker-compose logs -f"
    echo "   Stop app:    docker-compose down"
    echo "   Restart:     docker-compose restart"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Container failed to start${NC}"
    echo ""
    echo "Check logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "Or see TROUBLESHOOTING.md"
    exit 1
fi