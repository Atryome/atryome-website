#!/usr/bin/env bash
# Read-only local static-site audit. It never writes target files or contacts a network service.
set -uo pipefail

usage() { printf '%s\n' "Usage: $0 --root <repository> [--policy <KEY=VALUE file>]"; }
ROOT=""; POLICY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --root) ROOT="${2:-}"; shift 2 ;;
    --policy) POLICY="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'BLOCKER unknown argument: %s\n' "$1"; exit 2 ;;
  esac
done
[ -n "$ROOT" ] && [ -d "$ROOT" ] || { printf '%s\n' 'BLOCKER --root must name an existing directory'; exit 2; }
ROOT="$(cd "$ROOT" && pwd -P)"

blockers=0
emit() { local severity="$1"; shift; printf '%s %s\n' "$severity" "$*"; [ "$severity" = BLOCKER ] && blockers=$((blockers + 1)); return 0; }
is_boolean() { case "$1" in true|false|1|0|yes|no) return 0 ;; *) return 1 ;; esac; }
is_true() { case "$1" in true|1|yes) return 0 ;; *) return 1 ;; esac; }

policy_keys=(PUBLIC_DIR EXPECTED_ROUTES_FILE CANONICAL_BASE REQUIRE_CLEAN_WORKTREE REQUIRE_SITEMAP REQUIRE_ROBOTS_SITEMAP REQUIRE_METADATA REQUIRE_JS_SYNTAX SITEMAP_FILE ROBOTS_FILE)
policy_values=(. "" "" false false false false true sitemap.xml robots.txt)
policy_seen=(0 0 0 0 0 0 0 0 0 0)
boolean_keys=(REQUIRE_CLEAN_WORKTREE REQUIRE_SITEMAP REQUIRE_ROBOTS_SITEMAP REQUIRE_METADATA REQUIRE_JS_SYNTAX)
policy_index() {
  local key="$1" index
  for index in "${!policy_keys[@]}"; do [ "${policy_keys[$index]}" = "$key" ] && { printf '%s' "$index"; return 0; }; done
  return 1
}
is_boolean_key() {
  local key="$1" item
  for item in "${boolean_keys[@]}"; do [ "$item" = "$key" ] && return 0; done
  return 1
}
trim() { printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'; }
set_policy_value() {
  local key="$1" value="$2" index
  index="$(policy_index "$key")" || { emit BLOCKER "unknown policy key: $key"; return; }
  [ -n "$value" ] || { emit BLOCKER "empty value for policy key: $key"; return; }
  is_boolean_key "$key" && ! is_boolean "$value" && { emit BLOCKER "invalid boolean for $key: $value (accepted: true, false, 1, 0, yes, no)"; return; }
  if [ "${policy_seen[$index]}" = 1 ] && [ "${policy_values[$index]}" != "$value" ]; then emit BLOCKER "conflicting duplicate policy key: $key"; return; fi
  policy_values[$index]="$value"; policy_seen[$index]=1
}
policy_get() { printf '%s' "${policy_values[$(policy_index "$1")]}"; }

if [ -n "$POLICY" ]; then
  [ -f "$POLICY" ] || emit BLOCKER "policy file not found: $POLICY"
  if [ -f "$POLICY" ]; then
    policy_dir="$(cd "$(dirname "$POLICY")" && pwd -P)"; POLICY="$policy_dir/$(basename "$POLICY")"
    case "$POLICY" in "$ROOT"/*) ;; *) emit BLOCKER "policy file escapes repository root: $POLICY" ;; esac
  fi
fi
[ "$blockers" -eq 0 ] || exit 1
if [ -n "$POLICY" ]; then
  line_number=0
  while IFS= read -r raw || [ -n "$raw" ]; do
    line_number=$((line_number + 1)); line="$(trim "$raw")"
    case "$line" in ""|\#*) continue ;; esac
    case "$line" in *=*) key="$(trim "${line%%=*}")"; value="$(trim "${line#*=}")" ;; *) emit BLOCKER "malformed policy entry at line $line_number"; continue ;; esac
    [ -n "$key" ] || { emit BLOCKER "malformed policy entry at line $line_number"; continue; }
    set_policy_value "$key" "$value"
  done < "$POLICY"
fi
[ "$blockers" -eq 0 ] || exit 1

relative_path_is_safe() {
  case "$1" in /*) return 1 ;; esac
  case "/$1/" in *"/../"*) return 1 ;; esac
  return 0
}
resolve_existing_inside() {
  local base="$1" relative="$2" label="$3" resolved
  relative_path_is_safe "$relative" || { emit BLOCKER "$label escapes allowed root: $relative"; return 1; }
  [ -e "$base/$relative" ] || { emit BLOCKER "$label not found: $relative"; return 1; }
  resolved="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$base/$relative")" || { emit BLOCKER "$label cannot be resolved: $relative"; return 1; }
  case "$resolved" in "$base"|"$base"/*) RESOLVED_PATH="$resolved"; return 0 ;; *) emit BLOCKER "$label resolves outside allowed root: $relative"; return 1 ;; esac
}
validate_relative_path() { relative_path_is_safe "$2" || { emit BLOCKER "$1 escapes public root: $2"; return 1; }; return 0; }

RESOLVED_PATH=""
resolve_existing_inside "$ROOT" "$(policy_get PUBLIC_DIR)" "PUBLIC_DIR" || true
public_dir="$RESOLVED_PATH"
routes_file="$(policy_get EXPECTED_ROUTES_FILE)"
if [ -n "$routes_file" ]; then
  RESOLVED_PATH=""
  resolve_existing_inside "$ROOT" "$routes_file" "EXPECTED_ROUTES_FILE" || true
  routes_file="$RESOLVED_PATH"
fi
sitemap_file="$(policy_get SITEMAP_FILE)"; robots_file="$(policy_get ROBOTS_FILE)"
validate_relative_path SITEMAP_FILE "$sitemap_file" || true
validate_relative_path ROBOTS_FILE "$robots_file" || true
[ "$blockers" -eq 0 ] || exit 1

if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  emit INFO "Git worktree: $(git -C "$ROOT" rev-parse --show-toplevel)"
  is_true "$(policy_get REQUIRE_CLEAN_WORKTREE)" && [ -n "$(git -C "$ROOT" status --porcelain)" ] && emit BLOCKER "worktree is not clean"
else
  emit WARNING "audit root is not inside a Git worktree"
fi

args=(--root "$public_dir" --sitemap-file "$sitemap_file" --robots-file "$robots_file" --require-sitemap "$(policy_get REQUIRE_SITEMAP)" --require-robots "$(policy_get REQUIRE_ROBOTS_SITEMAP)" --require-metadata "$(policy_get REQUIRE_METADATA)")
[ -z "$routes_file" ] || args+=(--routes-file "$routes_file")
canonical_base="$(policy_get CANONICAL_BASE)"; [ -z "$canonical_base" ] || args+=(--canonical-base "$canonical_base")
python3 "$(dirname "$0")/validate_routes.py" "${args[@]}"; py_status=$?
[ "$py_status" -eq 0 ] || { printf '%s\n' 'BLOCKER audit failed during structural validation'; exit 1; }

sitemap_path="$public_dir/$sitemap_file"
if [ -f "$sitemap_path" ]; then
  if command -v xmllint >/dev/null 2>&1; then xmllint --noout "$sitemap_path" 2>/dev/null && emit INFO "sitemap XML accepted by xmllint" || emit BLOCKER "xmllint rejected sitemap XML: $sitemap_file"; else emit WARNING "xmllint unavailable; Python XML parsing was used"; fi
fi
if is_true "$(policy_get REQUIRE_JS_SYNTAX)"; then
  if command -v node >/dev/null 2>&1; then
    while IFS= read -r -d '' js_file; do node --check "$js_file" >/dev/null 2>&1 || emit BLOCKER "JavaScript syntax error: ${js_file#$public_dir/}"; done < <(find "$public_dir" -type f \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \) -print0)
    emit INFO "JavaScript syntax check completed"
  else
    emit WARNING "node unavailable; JavaScript syntax check skipped"
  fi
fi
[ "$blockers" -eq 0 ] && { printf '%s\n' 'INFO audit completed without deterministic blockers'; exit 0; }
printf 'BLOCKER audit failed with %s blocker(s)\n' "$blockers"; exit 1
