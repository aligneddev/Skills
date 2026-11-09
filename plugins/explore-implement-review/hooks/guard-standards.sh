#!/usr/bin/env bash
# PreToolUse guard: keeps the Standards away from the implementer subagent.
# Denies a tool call when the caller is the implementer and the call names a
# Standards path. Every other agent, and the main session, passes through.
#
# A guardrail, not a sandbox: a Bash command that reaches a Standards file
# without naming it (globs, variables, a broad grep) still gets through.

input=$(cat)

# Only the implementer is guarded: this plugin's agent or a repo override.
if ! printf '%s' "$input" | grep -Eq '"agent_type"[[:space:]]*:[[:space:]]*"(explore-implement-review:)?implementer"'; then
  exit 0
fi

# Keep in sync with the reviewer's sources in agents/reviewer.md.
# [/\\]+ matches / or a JSON-escaped Windows backslash.
standards='coding_standards\.md|docs[/\\]+agent([/\\"]|$)|\.specify[/\\]+memory([/\\"]|$)|contributing\.md'

tool_input=$(printf '%s' "$input" | sed -n 's/.*"tool_input"[[:space:]]*:\(.*\)/\1/p')

if printf '%s' "$tool_input" | grep -Eiq "$standards"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: the coding standards are reviewer-only. Do not try to read them another way; the reviewer checks standards after you. Carry on with the task."}}
EOF
fi

exit 0
