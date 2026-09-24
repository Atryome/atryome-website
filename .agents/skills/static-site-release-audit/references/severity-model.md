# Severity Model

## BLOCKER

A deterministic defect that makes the configured release scope invalid: missing required routes, broken internal routes or local assets, JavaScript syntax errors, malformed sitemap data, invalid JSON-LD, required metadata omissions, or a failed required Git cleanliness rule.

Any BLOCKER causes `audit-static-site.sh` to exit non-zero. Resolve it, explicitly adjust the consuming-project policy, or obtain documented release approval before proceeding.

## WARNING

A notable issue that needs review but is not automatically release-blocking under generic policy: missing optional metadata, missing optional sitemap or robots declaration, a tool unavailable for a requested check, or unresolved development markers.

## INFO

Context, coverage counts, skipped checks, and successful validation summaries.
