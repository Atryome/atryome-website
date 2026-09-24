# Aurora / ATRYOME static-site release visual QA

Perform human visual review only after deterministic audit checks pass. This document records review requirements; it does not automate approval.

## Routes

- `/`
- `/aurora/`
- `/aurora/development/`

## Target viewport widths

- 1600px
- 1200px
- 1024px
- 768px
- 430px
- 390px
- 375px
- 360px
- 320px

## Required checks

- No horizontal overflow, clipped primary content, unreadable text, or unusable controls.
- Header, navigation, footer, and internal route links remain usable.
- Local fonts, images, and media render as intended.
- ATMOSPHERE control accurately reflects its audio state; no form is submitted during review.
- The Early Community form retains its visible email, consent, honeypot, and submit controls; do not contact Brevo.
- With reduced motion enabled, essential content remains visible and meaningful without non-essential animation.
- Aurora Development progress values, gauges, and current-focus presentation match the owner-approved release scope.

Record route, viewport, browser, defect, reproduction notes, and review decision. Human approval is required before release readiness is declared.
