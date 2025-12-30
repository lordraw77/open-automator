#!/bin/bash
# Open-Automator Shell - Multi-Platform Docker Build & Push Script
# Supports: linux/amd64, linux/arm64

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-open-automator-shell}"
DOCKER_USERNAME="${DOCKER_USERNAME:-lordraw}"
REGISTRY="${REGISTRY:-docker.io}"
VERSION_MAJOR=2
VERSION_MINOR=1
VERSION_PATCH=0
VERSION="${VERSION:-${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}}"
DOCKERFILE="Dockerfile.shell"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
PUSH="${PUSH:-false}"  # Set to 'true' to push to registry

# Full image name with registry
FULL_IMAGE="${REGISTRY}/${DOCKER_USERNAME}/${IMAGE_NAME}"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Verify Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    log_info "Docker found: $(docker --version)"
}

# Verify buildx for multi-platform builds
check_buildx() {
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx not available!"
        log_info "Try: docker buildx create --use"
        exit 1
    fi
    log_info "Buildx available: $(docker buildx version | head -1)"
}

# Setup buildx builder
setup_builder() {
    local builder_name="oa-multiarch-builder"

    if ! docker buildx ls | grep -q "$builder_name"; then
        log_info "Creating multi-platform builder: $builder_name"
        docker buildx create --name "$builder_name" --use
        docker buildx inspect --bootstrap
    else
        log_info "Using existing builder: $builder_name"
        docker buildx use "$builder_name"
    fi
}

# Verify Dockerfile exists
check_dockerfile() {
    if [ ! -f "$DOCKERFILE" ]; then
        log_error "Dockerfile not found: $DOCKERFILE"
        exit 1
    fi
    log_info "Dockerfile found: $DOCKERFILE"
}

# Build the image
build_image() {
    log_section "BUILDING IMAGE"

    log_info "Configuration:"
    echo "  Image Name:    $IMAGE_NAME"
    echo "  Full Image:    $FULL_IMAGE"
    echo "  Version:       $VERSION"
    echo "  Platforms:     $PLATFORMS"
    echo "  Dockerfile:    $DOCKERFILE"
    echo "  Push:          $PUSH"
    echo ""

    local build_args=(
        "--platform" "$PLATFORMS"
        "--file" "$DOCKERFILE"
        "--tag" "${FULL_IMAGE}:${VERSION}"
        "--tag" "${FULL_IMAGE}:${VERSION_MAJOR}.${VERSION_MINOR}"
        "--tag" "${FULL_IMAGE}:${VERSION_MAJOR}"
        "--tag" "${FULL_IMAGE}:latest"
    )

    # Add build metadata
    build_args+=(
        "--label" "org.opencontainers.image.title=Open-Automator Shell"
        "--label" "org.opencontainers.image.description=CLI tool for running Open-Automator workflows"
        "--label" "org.opencontainers.image.version=${VERSION}"
        "--label" "org.opencontainers.image.vendor=Open-Automator"
        "--label" "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    )

    if [ "$PUSH" = "true" ]; then
        log_info "Building and pushing to registry..."
        build_args+=("--push")
    else
        log_info "Building locally (use PUSH=true to push to registry)..."
        # For local multi-arch, we need to use --load but only for single platform
        if [[ "$PLATFORMS" == *","* ]]; then
            log_warn "Multi-platform build without push detected"
            log_warn "Image will be pushed to local buildx cache only"
        else
            build_args+=("--load")
        fi
    fi

    # Build
    docker buildx build "${build_args[@]}" .

    if [ $? -eq 0 ]; then
        log_info "✅ Build successful!"
    else
        log_error "❌ Build failed!"
        exit 1
    fi
}

# Show image info
show_image_info() {
    log_section "IMAGE INFORMATION"

    if [ "$PUSH" = "true" ]; then
        log_info "Image pushed to registry:"
        echo "  📦 ${FULL_IMAGE}:${VERSION}"
        echo "  📦 ${FULL_IMAGE}:${VERSION_MAJOR}.${VERSION_MINOR}"
        echo "  📦 ${FULL_IMAGE}:${VERSION_MAJOR}"
        echo "  📦 ${FULL_IMAGE}:latest"
        echo ""
        log_info "Pull command:"
        echo "  docker pull ${FULL_IMAGE}:latest"
        echo ""
        log_info "Inspect multi-platform manifest:"
        echo "  docker buildx imagetools inspect ${FULL_IMAGE}:latest"
    else
        log_info "Local images created:"
        docker images | grep "$IMAGE_NAME" | head -5
    fi
}

# Display usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -p, --push              Push image to registry after build"
    echo "  -v, --version VERSION   Set version (default: ${VERSION})"
    echo "  -u, --username USER     Docker Hub username"
    echo "  --platforms PLATFORMS   Build platforms (default: linux/amd64,linux/arm64)"
    echo "  --single-platform       Build only for current platform (faster)"
    echo ""
    echo "Environment variables:"
    echo "  DOCKER_USERNAME         Docker Hub username"
    echo "  VERSION                 Image version"
    echo "  PLATFORMS              Build platforms"
    echo "  PUSH                   Set to 'true' to push"
    echo "  IMAGE_NAME             Image name (default: open-automator-shell)"
    echo ""
    echo "Examples:"
    echo "  # Local build (single platform)"
    echo "  $0 --single-platform"
    echo ""
    echo "  # Multi-platform build"
    echo "  $0"
    echo ""
    echo "  # Build and push to Docker Hub"
    echo "  DOCKER_USERNAME=myuser $0 --push"
    echo ""
    echo "  # Build specific version"
    echo "  $0 --version 1.2.0 --push"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--push)
            PUSH="true"
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -u|--username)
            DOCKER_USERNAME="$2"
            shift 2
            ;;
        --platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --single-platform)
            PLATFORMS="$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Update full image name with potentially changed username
FULL_IMAGE="${REGISTRY}/${DOCKER_USERNAME}/${IMAGE_NAME}"

# Main execution
main() {
    log_section "OPEN-AUTOMATOR SHELL - DOCKER BUILD"

    # Pre-flight checks
    check_docker
    check_buildx
    check_dockerfile
    setup_builder

    # Login if pushing
    if [ "$PUSH" = "true" ]; then
        if [ -z "$DOCKER_PASSWORD" ]; then
            log_info "Logging in to Docker Hub (interactive)..."
            docker login "$REGISTRY" -u "$DOCKER_USERNAME"
        else
            log_info "Logging in to Docker Hub (using DOCKER_PASSWORD)..."
            echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
        fi
    fi

    # Build
    build_image

    # Show results
    show_image_info

    log_section "✅ COMPLETED"
}

# Run
main
