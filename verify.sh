#!/bin/bash
# Build verification script

echo "=== Verifying project structure ==="
echo ""

# Check required files
REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yml"
    "app.py"
    "requirements.txt"
    "templates/index.html"
)

ALL_GOOD=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$(dirname "$file")" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
        ALL_GOOD=false
    fi
done

echo ""

if [ "$ALL_GOOD" = true ]; then
    echo "✅ All required files present!"
    echo ""
    echo "Ready to build. Run:"
    echo "  docker-compose build"
    echo "  docker-compose up -d"
else
    echo "❌ Some files are missing. Please check the structure."
    exit 1
fi