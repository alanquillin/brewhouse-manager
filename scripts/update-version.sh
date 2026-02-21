#!/bin/bash

# Script to update version number across all project files
# Usage: ./scripts/update-version.sh <version>
# Example: ./scripts/update-version.sh 1.0.0

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if version argument is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version argument is required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

VERSION="$1"

# Validate version format (basic semver check)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
    echo -e "${YELLOW}Warning: Version '$VERSION' does not match standard semver format (x.y.z)${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Updating version to ${VERSION}...${NC}"

# Update pyproject.toml
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
if [ -f "$PYPROJECT" ]; then
    sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$PYPROJECT"
    echo -e "  ${GREEN}✓${NC} Updated $PYPROJECT"
else
    echo -e "  ${RED}✗${NC} File not found: $PYPROJECT"
fi

# Update api/api.py
API_PY="$PROJECT_ROOT/api/api.py"
if [ -f "$API_PY" ]; then
    sed -i '' "s/version=\".*\",/version=\"$VERSION\",/" "$API_PY"
    echo -e "  ${GREEN}✓${NC} Updated $API_PY"
else
    echo -e "  ${RED}✗${NC} File not found: $API_PY"
fi

# Update ui/package.json
PACKAGE_JSON="$PROJECT_ROOT/ui/package.json"
if [ -f "$PACKAGE_JSON" ]; then
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$PACKAGE_JSON"
    echo -e "  ${GREEN}✓${NC} Updated $PACKAGE_JSON"
else
    echo -e "  ${RED}✗${NC} File not found: $PACKAGE_JSON"
fi

# Update ui/src/environments/environment.prod.ts
ENV_PROD="$PROJECT_ROOT/ui/src/environments/environment.prod.ts"
if [ -f "$ENV_PROD" ]; then
    sed -i '' "s/appVersion: ['\"].*['\"]/appVersion: '$VERSION'/" "$ENV_PROD"
    echo -e "  ${GREEN}✓${NC} Updated $ENV_PROD"
else
    echo -e "  ${RED}✗${NC} File not found: $ENV_PROD"
fi

echo -e "${GREEN}Version updated to ${VERSION} successfully!${NC}"
