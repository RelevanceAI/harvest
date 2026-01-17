#!/bin/bash
# Setup git hooks for Harvest repository
# Run once after cloning: bash scripts/setup-git-hooks.sh

set -e

echo "Setting up Harvest git hooks..."

# 1. Configure git to use shared hooks directory
echo "→ Configuring core.hooksPath..."
git config core.hooksPath .githooks

# 2. Create hooks directory if it doesn't exist
if [ ! -d ".githooks" ]; then
  echo "→ Creating .githooks directory..."
  mkdir -p .githooks
fi

# 3. Create pre-commit hook
echo "→ Creating pre-commit hook..."
cat > .githooks/pre-commit << 'EOF'
#!/bin/bash
# Prevent commits to protected branches

BRANCH=$(git branch --show-current)
PROTECTED_BRANCHES="^(main|master|develop)$"

if [[ "$BRANCH" =~ $PROTECTED_BRANCHES ]]; then
  echo "❌ ERROR: Direct commits to '$BRANCH' are not allowed."
  echo "   Create a feature branch first: git checkout -b <type>/<description>"
  echo "   Example: git checkout -b feat/add-feature"
  exit 1
fi
EOF

# 4. Create post-checkout hook (fallback warning)
echo "→ Creating post-checkout hook..."
cat > .githooks/post-checkout << 'EOF'
#!/bin/bash
# Warn if git hooks aren't configured correctly

HOOKS_PATH=$(git config --get core.hooksPath)
if [ "$HOOKS_PATH" != ".githooks" ]; then
  echo "⚠️  WARNING: Git hooks not configured!"
  echo "   Run: bash scripts/setup-git-hooks.sh"
fi

if [ ! -x ".githooks/pre-commit" ]; then
  echo "⚠️  WARNING: Pre-commit hook not executable!"
  echo "   Run: chmod +x .githooks/pre-commit"
fi
EOF

# 5. Make hooks executable
echo "→ Making hooks executable..."
chmod +x .githooks/pre-commit
chmod +x .githooks/post-checkout

echo "✅ Git hooks configured successfully!"
echo ""
echo "Protected branches: main, master, develop"
echo "All commits to these branches will be blocked."
