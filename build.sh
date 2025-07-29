#!/usr/bin/env bash

# A script to build, tag, and push a Docker image to a container registry.
#
# Usage: ./build.sh <tag>
# Example: ./build.sh v1.2.3

# --- Configuration ---
# Set your registry, owner (or namespace), and image name here.
readonly REGISTRY="ghcr.io"
readonly OWNER="morphobankorg"
readonly IMAGE_NAME="matrixcurator"
# ---------------------

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Colors for logging ---
readonly C_RESET='\033[0m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[0;33m'
readonly C_RED='\033[0;31m'

# --- Helper functions ---
log() {
  echo -e "${C_YELLOW}>> $1${C_RESET}"
}

success() {
  echo -e "${C_GREEN}✅ $1${C_RESET}"
}

error() {
  echo -e "${C_RED}❌ Error: $1${C_RESET}" >&2
  exit 1
}

# --- Argument Handling ---
# Check if a tag argument was provided.
if [[ -z "${1-}" ]]; then
  error "No tag specified.
Usage: $0 <tag>"
fi
readonly TAG="$1"

# --- Main Script Logic ---

# Construct the full image names
readonly FULL_IMAGE_NAME="${REGISTRY}/${OWNER}/${IMAGE_NAME}"
readonly TAGGED_IMAGE="${FULL_IMAGE_NAME}:${TAG}"
readonly LATEST_IMAGE="${FULL_IMAGE_NAME}:latest"

log "Starting Docker build and push process..."
echo "  - Full Image Name: ${FULL_IMAGE_NAME}"
echo "  - Tag to apply:    ${TAG}"
echo

# Step 1: Build the image
# We use two -t flags to apply both the specific tag and 'latest' tag at build time.
log "Building image with tags '${TAG}' and 'latest'..."
docker build -t "${TAGGED_IMAGE}" -t "${LATEST_IMAGE}" .
success "Build complete."
echo

# Step 2: Push the specific tag
log "Pushing tag '${TAG}' to ${REGISTRY}..."
docker push "${TAGGED_IMAGE}"
success "Pushed ${TAGGED_IMAGE}"
echo

# Step 3: Push the 'latest' tag
# Avoid pushing 'latest' twice if it was the specified tag.
if [[ "${TAG}" != "latest" ]]; then
  log "Pushing tag 'latest' to ${REGISTRY}..."
  docker push "${LATEST_IMAGE}"
  success "Pushed ${LATEST_IMAGE}"
  echo
fi

success "All tasks completed successfully!"