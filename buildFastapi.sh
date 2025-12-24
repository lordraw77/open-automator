#!/bin/bash
# Script per build Docker image Open-Automator fastapi

set -e  # Exit on error

# Configurazione
tag=open-automator-fastapi
minver=0
maxver=1
dockerfilename=Dockerfile.fastapi

VERSION="$maxver.$minver"
DOCKERFILE="$dockerfilename"
TAG="$tag"
echo "=========================================="
echo "Building Docker image"
echo "=========================================="
echo "Dockerfile: $dockerfilename"
echo "Tag: $tag:$maxver.$minver"
echo "=========================================="

# Verifica che il Dockerfile esista
if [ ! -f "$dockerfilename" ]; then
    echo "ERROR: Dockerfile not found: $dockerfilename"
    exit 1
fi

# Build con parametri corretti (tutto su una riga o con backslash)
if docker buildx version &> /dev/null; then
    echo "Using Docker Buildx"
    BUILD_CMD="docker buildx build"
else
    echo "Using standard Docker build"
    BUILD_CMD="docker build"
fi

echo "Starting build..."
$BUILD_CMD \
    -f "$DOCKERFILE" \
    -t "$TAG:$VERSION" \
    --no-cache \
    --compress \
    --force-rm \
    --load \
    .

# Verifica che il build sia riuscito
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""

    # Tag come latest
    docker tag "$tag:$maxver.$minver" "$tag:latest"

    echo "=========================================="
    echo "Images created:"
    echo "  - $tag:$maxver.$minver"
    echo "  - $tag:latest"
    echo "=========================================="

    # Mostra info immagine
    echo ""
    echo "Image details:"
    docker images | grep "$tag" | head -2

else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
