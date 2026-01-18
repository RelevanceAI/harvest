#!/bin/bash
# Validate that mode-specific files don't cross-reference each other

echo "Checking for cross-references between mode-specific files..."

# Check if local-development.md references autonomous-agent.md
if grep -q "autonomous-agent\.md" docs/ai/local-development.md; then
  echo "❌ FAIL: local-development.md references autonomous-agent.md"
  exit 1
fi

# Check if autonomous-agent.md references local-development.md
if grep -q "local-development\.md" docs/ai/autonomous-agent.md; then
  echo "❌ FAIL: autonomous-agent.md references local-development.md"
  exit 1
fi

# Check if claude.md exists (should, lowercase)
if [ ! -f .claude/claude.md ]; then
  echo "❌ FAIL: .claude/claude.md should exist"
  exit 1
fi

echo "✅ PASS: Mode-specific files are properly separated"
exit 0
