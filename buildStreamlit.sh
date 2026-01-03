#!/bin/bash
#
# Open-Automator Streamlit - Multi-platform Docker Build & Push Script
# Supports: linux/amd64, linux/arm64
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKERFILE="${DOCKERFILE:-Dockerfile.streamlit}"
IMAGE_NAME="${IMAGE_NAME:-open-automator-streamlit}"
DOCKER_USERNAME="${DOCKER_USERNAME:-lordraw}"
VERSION="${VERSION:-3.0.0}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILDER_NAME="multiarch-builder"

# Parse version
IFS='.' read -r VERSION_MAJOR VERSION_MINOR VERSION_PATCH <<< "$VERSION"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Build and optionally push Open-Automator Streamlit Docker image for multiple platforms.

OPTIONS:
    --help                  Show this help message
    --push                  Push to Docker Hub after build
    --version VERSION       Set version (default: 1.0.0)
    --username USERNAME     Docker Hub username (or set DOCKER_USERNAME env var)
    --platforms PLATFORMS   Target platforms (default: linux/amd64,linux/arm64)
    --single-platform       Build only for current platform (faster for testing)
    --no-cache              Build without cache

ENVIRONMENT VARIABLES:
    DOCKER_USERNAME         Docker Hub username
    VERSION                 Image version (default: 1.0.0)
    IMAGE_NAME              Base image name (default: open-automator-streamlit)
    PLATFORMS               Target platforms
    DOCKERFILE              Dockerfile path (default: Dockerfile.streamlit)

EXAMPLES:
    # Build multi-platform (no push)
    $0

    # Build and push
    DOCKER_USERNAME=myuser $0 --push

    # Build specific version and push
    $0 --version 1.2.3 --username myuser --push

    # Quick test build (current platform only)
    $0 --single-platform

    # Build without cache
    $0 --no-cache

TAGS CREATED:
    - USERNAME/open-automator-streamlit:1.0.0      (full version)
    - USERNAME/open-automator-streamlit:1.0        (major.minor)
    - USERNAME/open-automator-streamlit:1          (major)
    - USERNAME/open-automator-streamlit:latest     (latest)

EOF
}

# Parse arguments
PUSH=false
NO_CACHE=""
SINGLE_PLATFORM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --version)
            VERSION="$2"
            IFS='.' read -r VERSION_MAJOR VERSION_MINOR VERSION_PATCH <<< "$VERSION"
            shift 2
            ;;
        --username)
            DOCKER_USERNAME="$2"
            shift 2
            ;;
        --platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --single-platform)
            SINGLE_PLATFORM=true
            shift
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validation
if [ ! -f "$DOCKERFILE" ]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

if [ "$PUSH" = true ] && [ -z "$DOCKER_USERNAME" ]; then
    print_error "Docker username required for push. Set DOCKER_USERNAME or use --username"
    exit 1
fi

# Set full image name
if [ -n "$DOCKER_USERNAME" ]; then
    FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME"
else
    FULL_IMAGE="$IMAGE_NAME"
fi

# Single platform mode
if [ "$SINGLE_PLATFORM" = true ]; then
    PLATFORMS=$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')
    print_info "Single-platform mode: $PLATFORMS"
fi

# Print configuration
print_header "Open-Automator Streamlit Build"
echo "Dockerfile:    $DOCKERFILE"
echo "Image:         $FULL_IMAGE"
echo "Version:       $VERSION"
echo "Platforms:     $PLATFORMS"
echo "Push:          $PUSH"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found"
    exit 1
fi

print_success "Docker found"

# Check buildx
if ! docker buildx version &> /dev/null; then
    print_error "Docker buildx not available"
    exit 1
fi

print_success "Docker buildx available"

# Create/use builder
print_info "Setting up buildx builder..."
if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
    print_success "Builder created: $BUILDER_NAME"
else
    docker buildx use "$BUILDER_NAME"
    print_success "Using existing builder: $BUILDER_NAME"
fi

# Docker login if pushing
if [ "$PUSH" = true ]; then
    print_info "Logging in to Docker Hub..."
    if ! docker login; then
        print_error "Docker login failed"
        exit 1
    fi
    print_success "Logged in to Docker Hub"
fi

# Build
print_header "Building Image"

BUILD_ARGS=(
    "build"
    "-f" "$DOCKERFILE"
    "--platform" "$PLATFORMS"
    "--tag" "${FULL_IMAGE}:${VERSION}"
    "--tag" "${FULL_IMAGE}:${VERSION_MAJOR}.${VERSION_MINOR}"
    "--tag" "${FULL_IMAGE}:${VERSION_MAJOR}"
    "--tag" "${FULL_IMAGE}:latest"
    "--label" "org.opencontainers.image.title=Open-Automator Streamlit"
    "--label" "org.opencontainers.image.description=Web UI for Open-Automator workflow management"
    "--label" "org.opencontainers.image.version=${VERSION}"
    "--label" "org.opencontainers.image.vendor=Open-Automator"
    "--label" "org.opencontainers.image.url=https://hub.docker.com/r/${FULL_IMAGE}"
)

if [ -n "$NO_CACHE" ]; then
    BUILD_ARGS+=("$NO_CACHE")
fi

if [ "$PUSH" = true ]; then
    BUILD_ARGS+=("--push")
else
    BUILD_ARGS+=("--load")
fi

BUILD_ARGS+=(".")

echo "Command: docker buildx ${BUILD_ARGS[*]}"
echo ""

if docker buildx "${BUILD_ARGS[@]}"; then
    echo ""
    print_success "Build completed successfully!"

    echo ""
    print_header "Image Details"
    echo "Tags created:"
    echo "  • ${FULL_IMAGE}:${VERSION}"
    echo "  • ${FULL_IMAGE}:${VERSION_MAJOR}.${VERSION_MINOR}"
    echo "  • ${FULL_IMAGE}:${VERSION_MAJOR}"
    echo "  • ${FULL_IMAGE}:latest"
    echo ""
    echo "Platforms: $PLATFORMS"

    if [ "$PUSH" = true ]; then
        echo ""
        print_success "Images pushed to Docker Hub!"
        echo ""
        print_info "Verify with:"
        echo "  docker pull ${FULL_IMAGE}:latest"
        echo "  docker buildx imagetools inspect ${FULL_IMAGE}:latest"
        echo ""
        print_info "View on Docker Hub:"
        echo "  https://hub.docker.com/r/${FULL_IMAGE}"
    else
        echo ""
        print_info "Images built locally (not pushed)"
        echo ""
        print_info "To push, run:"
        echo "  $0 --push"
    fi

    echo ""
    print_header "Quick Start"
    echo "Run container:"
    echo "  docker run -p 8501:8501 ${FULL_IMAGE}:latest"
    echo ""
    echo "With volumes:"
    echo "  docker run -p 8501:8501 \\"
    echo "    -v \$(pwd)/workflows:/app/workflows \\"
    echo "    -v \$(pwd)/data:/app/data \\"
    echo "    ${FULL_IMAGE}:latest"

else
    echo ""
    print_error "Build failed!"
    exit 1
fi
