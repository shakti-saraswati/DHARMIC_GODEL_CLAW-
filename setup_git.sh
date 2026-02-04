#!/bin/bash
# DHARMIC GÖDEL CLAW - Git Setup Script
# Run this once to configure git for vijnan-shakti identity

set -e

echo "🔥 DHARMIC GÖDEL CLAW - Git Configuration"
echo "=========================================="

# Load environment
if [ -f ~/.env ]; then
    export $(grep -v '^#' ~/.env | xargs)
    echo "✅ Loaded ~/.env"
else
    echo "❌ ~/.env not found"
    exit 1
fi

# Configure git identity for this project
git config --global user.name "vijnan-shakti"
git config --global user.email "vijnan.shakti@proton.me"
git config --global core.excludesfile ~/.gitignore_global

echo "✅ Git identity configured:"
echo "   Name:  $(git config --global user.name)"
echo "   Email: $(git config --global user.email)"

# Test GitHub token
echo ""
echo "Testing GitHub token..."
RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user)
USERNAME=$(echo $RESPONSE | grep -o '"login":"[^"]*"' | cut -d'"' -f4)

if [ -n "$USERNAME" ]; then
    echo "✅ GitHub authenticated as: $USERNAME"
else
    echo "❌ GitHub authentication failed"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Store credentials for HTTPS
git config --global credential.helper store
echo "https://$USERNAME:$GITHUB_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
echo "✅ Git credentials stored securely"

echo ""
echo "🔥 Setup complete! Ready to clone and build."
echo ""
echo "Next: Run ./clone_all.sh to pull OpenClaw, DGM, Agno"
