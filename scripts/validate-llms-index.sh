#!/bin/bash
# Validates llms.txt references

set -e

echo "Validating llms.txt..."

# Extract all file paths from llms.txt (markdown links format)
PATHS=$(grep -oE '\]\([^)]+\)' llms.txt | sed 's/](\(.*\))/\1/')

ERRORS=0
for path in $PATHS; do
  if [ ! -f "$path" ]; then
    echo "❌ Missing file: $path"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ $ERRORS -eq 0 ]; then
  echo "✅ All llms.txt references valid"
  exit 0
else
  echo "❌ Found $ERRORS broken references in llms.txt"
  exit 1
fi
