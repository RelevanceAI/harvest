#!/bin/bash
# Validate that mode-specific files don't cross-reference each other
#
# Structure:
# - docs/ai/agent.md: Local development rules (used in repo)
# - docs/ai/autonomous-agent.md: Autonomous rules (copied as agent.md in container build)
# These files should not reference each other to maintain clean separation.
#
# Note: We check for actual file references (markdown links, @ references) not mentions
# in documentation/comments. This allows explaining the build-time replacement.

echo "Checking for cross-references between mode-specific files..."

# Check if agent.md has actual references to autonomous-agent.md
# (markdown links or @ references, not prose mentions)
if grep -E '\(@?docs/ai/autonomous-agent\.md\)|\[@?docs/ai/autonomous-agent\.md\]|`@docs/ai/autonomous-agent\.md`' docs/ai/agent.md; then
  echo "❌ FAIL: agent.md has link/reference to autonomous-agent.md"
  exit 1
fi

# Check if autonomous-agent.md has actual references to agent.md
# (markdown links or @ references)
if grep -E '\(@?docs/ai/agent\.md\)|\[@?docs/ai/agent\.md\]|`@docs/ai/agent\.md`' docs/ai/autonomous-agent.md; then
  echo "❌ FAIL: autonomous-agent.md has link/reference to agent.md"
  exit 1
fi

# Check if claude.md exists (should, lowercase)
if [ ! -f .claude/claude.md ]; then
  echo "❌ FAIL: .claude/claude.md should exist"
  exit 1
fi

echo "✅ PASS: Mode-specific files are properly separated"
exit 0
