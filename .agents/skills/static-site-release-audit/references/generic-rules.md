# Generic Rules

Run the audit against an explicit local repository root and its static public directory. The optional policy file must be inside that repository and is UTF-8 plain text with one `KEY=VALUE` entry per line; blank lines and lines beginning with `#` are ignored. Values are data, never executed. Unknown keys, empty values, malformed entries, and conflicting duplicate keys are BLOCKERs. Accepted boolean values are exactly `true`, `false`, `1`, `0`, `yes`, and `no`.

| Key | Meaning | Default |
|---|---|---|
| `PUBLIC_DIR` | Existing public directory relative to audit root | audit root |
| `EXPECTED_ROUTES_FILE` | Existing route file relative to audit root; one public route per line | none |
| `CANONICAL_BASE` | Required absolute canonical origin | none |
| `REQUIRE_CLEAN_WORKTREE` | Require no uncommitted Git changes | `false` |
| `REQUIRE_SITEMAP` | Missing sitemap is a BLOCKER | `false` |
| `REQUIRE_ROBOTS_SITEMAP` | Missing `Sitemap:` declaration is a BLOCKER | `false` |
| `REQUIRE_METADATA` | Missing title, description, Open Graph, or Twitter metadata is a BLOCKER | `false` |
| `REQUIRE_JS_SYNTAX` | JavaScript syntax validation is required when Node is available | `true` |
| `SITEMAP_FILE` | Sitemap path relative to public directory | `sitemap.xml` |
| `ROBOTS_FILE` | Robots path relative to public directory | `robots.txt` |

All configured paths must remain inside the applicable repository or public root after symlink resolution. Routes use URL paths, one per line, such as `/`, `/about/`, or `/contact`; `/about` and `/about/` are equivalent. Route-to-file mapping accepts `route/index.html`, `route.html`, or an exact file path where appropriate. Policy owners decide whether a route is public; the generic skill does not infer a client’s information architecture.

## Deterministic checks

The scripts inspect only local files and Git state. They check Git worktree identity and optional cleanliness; expected route existence; internal HTML links and local assets; JavaScript syntax; sitemap XML and route consistency; robots sitemap declarations; canonical links; titles; descriptions; Open Graph and Twitter metadata; JSON-LD syntax; and obvious `localhost`, `debugger`, or `console.log` markers.

The checks are structural. They do not prove visual layout, runtime behavior, accessibility conformance, link destination quality, content accuracy, or third-party service behavior. Version 1 does not parse `srcset` values or CSS `url(...)` references; review those during AI-assisted or human QA.
