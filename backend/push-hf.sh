#!/bin/bash

# Script to push backend to HuggingFace from the backend directory
# This script should be run from the backend directory
# Usage: ./push-to-hf.sh

echo "🚀 Pushing backend to HuggingFace Spaces..."

# Go to root directory
cd ..

# Create a new subtree split for backend
git subtree split --prefix=backend -b backend-hf-$(date +%Y%m%d-%H%M%S)

# Get the latest branch name
LATEST_BRANCH=$(git branch | grep "backend-hf-" | tail -1 | sed 's/^..//')

echo "📦 Created branch: $LATEST_BRANCH"

# Push to HuggingFace
git push hf $LATEST_BRANCH:main --force

echo "✅ Backend successfully pushed to HuggingFace Spaces!"
echo "🔗 View at: https://huggingface.co/spaces/BinKhoaLe1812/Cooking_Tutor"

# Clean up the temporary branch
git branch -D $LATEST_BRANCH
echo "🧹 Cleaned up temporary branch: $LATEST_BRANCH"

# Return to backend directory
cd backend
