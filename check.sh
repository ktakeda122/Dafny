#!/usr/bin/env bash
# Verify one method body against one spec, the same way repair_loop.py does.
# Usage: ./check.sh LinearSearch.spec.dfy wrong/LastOccurrence.body.dfy
set -euo pipefail
tmp=$(mktemp -d)
{ cat "$1"; echo; cat "$2"; } > "$tmp/Candidate.dfy"
dafny verify "$tmp/Candidate.dfy"
