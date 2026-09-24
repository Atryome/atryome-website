# Human Visual QA Matrix

Human review is required because file-level validation cannot establish rendering quality. The consuming project supplies browsers, viewports, representative pages, and acceptance criteria.

| Area | Review question |
|---|---|
| Primary routes | Do configured public pages render and communicate the intended hierarchy? |
| Responsive layout | Does the layout remain usable at project-defined viewport sizes and orientations? |
| Navigation | Are menus, visible links, focus states, and back/forward flows understandable? |
| Content | Are copy, images, calls to action, legal notices, and contact paths current and intentional? |
| Accessibility | Are keyboard interaction, contrast, text scaling, labels, and motion behavior reasonable for the release scope? |
| Cross-browser | Does the project-defined browser set render without visible breakage? |
| Release evidence | Are screenshots or review notes captured according to the consuming project process? |

Record defects with route, viewport/browser, reproduction steps, evidence, and severity. Do not substitute AI inference for human visual acceptance.
