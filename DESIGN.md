# Design

UFC should feel like a playful but still finance-aware group dashboard: bright, tactile, and easy to scan, like a stack of toy building blocks that each hold one piece of the group's spending story.

## Visual Direction

- Use a white mobile-first canvas with a compact status/header area.
- Build the primary dashboard from glossy block modules with visible studs along the top edge.
- Use strong block colors by information type:
  - Blue: main financial DNA and optimization suggestions
  - Yellow: tendency scores and acceleration suggestions
  - Red: AI insight narrative
  - Green: goal progress
  - Orange: recommended financial products
  - White: similar financial DNA comparisons
- Cards should feel dimensional through layered highlights, inset borders, and soft shadows, while keeping border radius at 8px or less.
- Avoid generic SaaS cards for the main dashboard. The block shape is the core UI language.

## Screen Composition

Primary first screen: `Unity Finance Crew` dashboard.

- Top header:
  - UFC gradient wordmark
  - Product name: `Unity Finance Crew`
  - Subtitle: `함께 쌓아가는 우리들의 금융 여정`
  - Notification and menu controls
- Hero block:
  - Label: `금융 DNA`
  - Primary type: `ESTJ`
  - Descriptor: `전략적 소비자`
  - Short explanation
  - Circular confidence meter around `91%`
- Analysis row:
  - Yellow tendency block with 4 horizontal score bars
  - Red AI insight block with 3 compact insight rows
- Goal builder block:
  - Green progress block for a shared goal such as `일본 여행`
  - Large progress percentage, current/target amount, expected date, and staged progress bricks
- Suggestion row:
  - Blue optimization proposal
  - Yellow acceleration proposal
- Product recommendation row:
  - Orange recommendation blocks with match percentages and arrow actions
- Similar DNA strip:
  - White base block with small colored comparison chips

## Interaction Principles

- The dashboard must be readable without onboarding copy.
- Each block should expose one decision or status at a glance.
- Financial amounts and percentages should be large enough to scan on mobile.
- Server-calculated data will replace mock values in later phases; FE does not calculate authoritative MBTI or spending scores.
- The preview route may use mock display values only for design iteration.

## Responsive Rules

- Mobile width is the primary target. The dashboard should resemble a tall app screenshot.
- On larger screens, center the mobile canvas rather than stretching every block edge-to-edge.
- Two-column rows collapse into one column below narrow widths.
- Studs, progress bricks, bars, and text must not resize the layout unexpectedly.
