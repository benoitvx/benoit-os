#!/usr/bin/env bash
# Find the current Claude Code session ID by locating the most recently
# modified .jsonl file in ~/.claude/projects/<encoded-cwd>/.
#
# Encoding: any character not in [A-Za-z0-9] is replaced by '-'.
# Example: /Users/foo/Mon Drive  ->  -Users-foo-Mon-Drive
#
# Usage: get_session_id.sh [cwd]
# Output (stdout): <session-uuid>
# Exit codes: 0 ok, 1 project dir not found, 2 no .jsonl found

set -e

CWD="${1:-$PWD}"
# Resolve symlinks: Claude Code keys sessions on the real path.
RESOLVED=$(cd "$CWD" 2>/dev/null && pwd -P) || RESOLVED="$CWD"
ENCODED=$(printf '%s' "$RESOLVED" | sed 's/[^A-Za-z0-9]/-/g')
PROJECT_DIR="$HOME/.claude/projects/$ENCODED"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "ERROR: project dir not found: $PROJECT_DIR" >&2
  exit 1
fi

LATEST=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -n 1)

if [ -z "$LATEST" ]; then
  echo "ERROR: no .jsonl session file in $PROJECT_DIR" >&2
  exit 2
fi

basename "$LATEST" .jsonl
