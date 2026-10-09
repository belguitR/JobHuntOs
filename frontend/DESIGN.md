# Job Hunt OS Design Direction

## Product character

Job Hunt OS is a private, focused operating system for an emotionally demanding process. It should feel calm, capable, editorial, and quietly ambitious. The interface is an operating tool first and a brand experience second.

Core idea: **one operational workspace for every country in a job search**.

## Visual language

- Warm paper canvas rather than clinical white.
- Deep aubergine navigation creates a stable frame around the workspace.
- Plum is reserved for primary actions, current state, and meaningful focus.
- Clay, rose, and muted brown add warmth without becoming decorative noise.
- Newsreader is the editorial voice for page titles and moments of encouragement. DM Sans carries operational UI.
- Default surfaces are nearly flat: one-pixel warm borders and very soft shadows. Strong elevation is reserved for overlays and active transitions.
- Geometry is sober: 7–12px radii for controls and cards. Avoid universal pills, glass cards, excessive gradients, and nested cards.

## Core tokens

| Role | Value |
| --- | --- |
| Canvas | `#f7f3ed` |
| Surface | `#fffcf8` |
| Ink | `#2c2230` |
| Muted | `#786a77` |
| Hairline | `#e4dbd5` |
| Plum | `#65416f` |
| Aubergine | `#241827` |
| Clay | `#a87061` |
| Rose | `#bc8985` |

Spacing follows a 4px base with 8, 12, 16, 20, 24, 32, and 48px as the main rhythm.

## Motion direction

Motion communicates place, continuity, and cause. It must never delay a frequent action.

- Micro feedback: 140–220ms.
- Page and panel entrances: 320–480ms with an exponential ease-out.
- Spatial transitions: damped springs, no bounce unless celebrating a completed action.
- Stagger groups by 45–70ms. Keep total choreography under 700ms.
- Animate transform and opacity by default. Use layout animation for filtering, reordering, and shared selection state.
- Country selection is the signature moment: the globe moves first, the chosen market highlights, then strategy controls reveal.
- New records receive one restrained confirmation moment. Routine saves should remain quiet.
- Pointer parallax is permitted only on expressive onboarding surfaces and must stay under three degrees.
- Respect `prefers-reduced-motion`; preserve information and state without movement.

## Interaction rules

- Every interactive element needs hover, active, focus-visible, disabled, and error behavior.
- Hover should clarify clickability through one subtle signal: lift, tint, border, or directional movement—not all four.
- Primary actions use plum and appear once per decision area.
- Tables prioritize scanning and keep controls stable as content changes.
- Empty states teach the next useful action without fake data.
- Responsive layouts preserve task order; decorative elements can simplify before content does.

## Anti-patterns

- No generic gradient headline, floating blob collection, fake testimonial, or vanity metric.
- No constant motion in dense work areas.
- No animation on every card at every render.
- No icon-only action without an accessible label.
- No copied brand identity. References inform rigor and system quality, not imitation.
