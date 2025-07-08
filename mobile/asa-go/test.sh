#!/bin/bash

# Minimal Keycloak Test Runner
# Runs the Keycloak Swift Package tests directly

set -e

# Configuration
KEYCLOAK_PACKAGE_DIR="../keycloak"
SIMULATOR_NAME="iPhone 16 Pro"

# Check if we're in the right directory
if [ ! -d "$KEYCLOAK_PACKAGE_DIR" ]; then
    echo "❌ Error: Could not find Keycloak package at $KEYCLOAK_PACKAGE_DIR"
    echo "Please run this script from the asa-go project root directory"
    exit 1
fi

echo "🧪 Running Keycloak Swift Package Tests"
echo "======================================="

# Navigate to the Keycloak package directory
cd "$KEYCLOAK_PACKAGE_DIR"

# Run tests with xcodebuild (supports iOS properly)
echo "🧪 Running Keycloak tests..."

xcodebuild test \
    -scheme "Keycloak" \
    -destination "platform=iOS Simulator,name=$SIMULATOR_NAME"

echo "🎉 Tests completed successfully!"
