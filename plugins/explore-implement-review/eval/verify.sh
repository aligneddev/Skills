#!/usr/bin/env bash
# Independent check of a commit: exports it to a clean dir, runs the backend tests and the
# frontend lint, typecheck/build and unit tests. Does not trust anything an agent reported.
#   verify.sh <repo> <sha> <out-file>
set -uo pipefail
repo=$1 sha=$2 out=$3
FE_LINUX="${FE_LINUX:-$HOME/biketracking-frontend-linux}"
dir=$(mktemp -d "${TMPDIR:-/tmp}/verify-XXXX")
git -C "$repo" archive "$sha" | tar -x -C "$dir"
ln -s "$FE_LINUX/node_modules" "$dir/src/BikeTracking.Frontend/node_modules"

{
  echo "## verify $sha"
  (cd "$dir" && dotnet test BikeTracking.slnx 2>&1 | grep -E "^(Passed!|Failed!)|error " | head -20)
  echo "backend_exit=${PIPESTATUS[0]}"
  cd "$dir/src/BikeTracking.Frontend"
  for s in lint build test:unit; do
    npm run -s "$s" > "$dir/$s.log" 2>&1; rc=$?
    echo "frontend_${s//:/_}_exit=$rc"
    grep -E "Tests +[0-9]+|Test Files|error|✖" "$dir/$s.log" | tail -4
  done
} > "$out" 2>&1
rm -rf "$dir"
cat "$out"
