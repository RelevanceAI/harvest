#!/bin/bash
# Validates llms.txt references using git index (case-sensitive across all platforms)

set -e

echo "Validating llms.txt..."

# Extract all file paths from llms.txt (markdown links format)
PATHS=$(grep -oE '\]\([^)]+\)' llms.txt | sed 's/](\(.*\))/\1/')

ERRORS=0
for path in $PATHS; do
  # Check if file exists in git index (case-sensitive, platform-independent)
  if ! git ls-files --error-unmatch "$path" &>/dev/null; then
    echo "❌ Missing or not tracked in git: $path"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ $ERRORS -eq 0 ]; then
  echo "✅ All llms.txt references valid and tracked in git"
  exit 0
else
  echo "❌ Found $ERRORS broken references in llms.txt"
  exit 1
fi
