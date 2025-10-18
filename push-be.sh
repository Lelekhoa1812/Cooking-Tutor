#!/bin/bash

# Script to push only the backend folder to HuggingFace Spaces
# Usage: ./push-backend.sh

echo "🚀 Pushing backend to HuggingFace Spaces..."

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
