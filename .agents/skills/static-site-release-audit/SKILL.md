---
name: static-site-release-audit
description: Audit a static website release for local route, asset, metadata, sitemap, and release-readiness defects before deployment.
---

# Static Site Release Audit

Use this skill for release validation of an already-built or source-controlled static website. It is vendor-neutral: obtain the target repository, public directory, expected routes, canonical host, and release policy from the consuming project. Do not invent project-specific requirements.

## Safety boundary

Audit local files only. Do not modify source, submit forms, contact external services, deploy, commit, push, alter Git configuration, or read credentials. Stop before any action outside this boundary and ask for authorization.

## Workflow

1. Establish the audit scope from the consuming project’s policy and Git worktree. Read [generic rules](references/generic-rules.md) and [severity model](references/severity-model.md).
2. Run `scripts/audit-static-site.sh --root <repository> [--policy <policy-file>]`. Treat a non-zero exit as a deterministic BLOCKER outcome.
3. Review findings that require judgment: content accuracy, calls to action, legal claims, accessibility semantics, responsive behavior, and anything intentionally excluded by policy.
4. Conduct human visual review using [the visual QA matrix](references/visual-qa-matrix.md) in the actual target browsers and viewports specified by the consuming project.
5. Report deterministic findings separately from AI-assisted observations and human visual-review results. Do not declare release readiness if any BLOCKER remains.

The script accepts a simple `KEY=VALUE` policy file; it never sources it as shell code. Keep client-specific routes, canonical host, and visual requirements in the consuming repository, not this skill.

## Reference routing

- Read [generic rules](references/generic-rules.md) before configuring or interpreting deterministic checks.
- Read [severity model](references/severity-model.md) when triaging or reporting findings.
- Read [visual QA matrix](references/visual-qa-matrix.md) only for the human visual-review stage.
