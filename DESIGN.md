---
name: AQuantLens US Options Workbench
description: Institution-grade Chinese-first research workbench for U.S. equities, options, and paper-only validation.
colors:
  background: "oklch(1 0 0)"
  foreground: "oklch(0.145 0 0)"
  card: "oklch(1 0 0)"
  primary: "oklch(0.205 0 0)"
  primary-foreground: "oklch(0.985 0 0)"
  secondary: "oklch(0.97 0 0)"
  muted: "oklch(0.97 0 0)"
  muted-foreground: "oklch(0.556 0 0)"
  border: "oklch(0.922 0 0)"
  destructive: "oklch(0.577 0.245 27.325)"
  positive: "#16a34a"
  negative: "#dc2626"
  chart-blue: "#2563eb"
  chart-violet: "#7c3aed"
  chart-axis: "#64748b"
  chart-grid-strong: "rgba(148, 163, 184, 0.22)"
  chart-grid-soft: "rgba(148, 163, 184, 0.16)"
typography:
  headline:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0"
  title:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.375
    letterSpacing: "0"
  body:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.333
    letterSpacing: "0"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.md}"
    height: "32px"
    padding: "0 10px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "32px"
    padding: "0 10px"
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.xl}"
    padding: "16px"
  input:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "40px"
---

# Design System: AQuantLens US Options Workbench

## 1. Overview

**Creative North Star: "Research Control Room"**

AQuantLens should feel like a serious internal research control room: calm, compact, and explicit about what is evidence, what is review, and what is paper-only simulation. The interface is not trying to impress public investors; it is trying to help an expert operator move through market data, AI research, strategy candidates, and paper workflows without losing the thread.

The system uses one disciplined sans family, mostly neutral surfaces, tight component geometry, and low-drama state color. Density is allowed because the product is an expert workbench, but every dense region must still provide clear hierarchy, recoverable errors, keyboard-visible focus, and paper/live boundaries that cannot be mistaken.

It explicitly rejects public trading-app energy, broker execution-console affordances, live-order language, promotional SaaS dashboard gloss, fake static dashboard data, and decorative finance theatrics.

**Key Characteristics:**
- Restrained neutral palette with rare primary emphasis.
- Dense but structured workbench layouts.
- Status labels paired with icons or text, never color alone.
- Paper-only workflow boundaries repeated at decision points.
- Tables, cards, and controls use shared shadcn/Tailwind primitives.

## 2. Colors

The palette is a neutral institutional system: black, white, and gray OKLCH tokens carry most surfaces, while semantic green/red and a small chart pair support market and signal meaning.

### Primary
- **Workbench Ink** (`oklch(0.205 0 0)`): Primary actions, selected navigation, high-confidence current state, and compact icon blocks.

### Secondary
- **Review Blue** (`#2563eb`): Chart fast moving average and analytical overlays where a distinct series is required.
- **Model Violet** (`#7c3aed`): Chart slow moving average or secondary analytical overlay. Use sparingly; do not let violet become a decorative brand gradient.
- **Axis Slate** (`#64748b`): Chart axis text and volume series when it needs to recede behind price and signal data.
- **Grid Slate** (`rgba(148, 163, 184, 0.22)` / `rgba(148, 163, 184, 0.16)`): Lightweight chart grid lines and chart borders only.

### Neutral
- **Canvas White** (`oklch(1 0 0)`): Main background and card surface in light mode.
- **Institution Ink** (`oklch(0.145 0 0)`): Primary text.
- **Muted Rail** (`oklch(0.97 0 0)`): Secondary panels, hover fills, and low-emphasis metric tiles.
- **Operational Gray** (`oklch(0.556 0 0)`): Secondary text; avoid going lighter for body copy.
- **Divider Gray** (`oklch(0.922 0 0)`): Borders, inputs, table dividers, and structural separation.

### Tertiary
- **Pass Green** (`#16a34a`): Positive market direction, buy/pass states, and gains. Pair with text labels.
- **Block Red** (`#dc2626` / `oklch(0.577 0.245 27.325)`): Destructive actions, rejected status, failed risk checks, and down moves. Pair with text labels.

### Named Rules
**The Evidence-First Rule.** Color is for state, selection, chart series, and risk meaning only. It is not decoration.

**The No-Ambiguous-Green Rule.** Green can mean positive market direction or a passed check only when the label also says the state.

## 3. Typography

**Display Font:** Geist Variable, sans-serif  
**Body Font:** Geist Variable, sans-serif  
**Label/Mono Font:** Geist Variable, sans-serif

**Character:** A single-family product system: crisp, compact, and predictable. The typography should support scanning and comparison rather than editorial drama.

### Hierarchy
- **Headline** (600, 1.25rem, 1.25): Page and major panel titles such as Strategy Lab.
- **Title** (500, 1rem, 1.375): Card titles, table group headings, and compact section labels.
- **Body** (400, 0.875rem, 1.5): Operational descriptions, table body text, status explanations, and empty states.
- **Label** (500, 0.75rem, 1.333): Form labels, metric captions, badges, and secondary metadata.

### Named Rules
**The Fixed-Scale Rule.** Product UI headings use fixed rem sizes, not fluid hero scales.

**The Label Clarity Rule.** Labels and buttons use normal letter spacing. Do not add uppercase tracking as decoration.

## 4. Elevation

The system is flat by default and uses tonal layering, borders, and ring outlines instead of ambient shadows. Depth comes from surface contrast (`bg-card`, `bg-muted/20`, `bg-background`) and clear boundaries, not floating cards.

### Shadow Vocabulary
- **None at rest:** Cards and panels use `ring-1`, `border`, or tonal fill.
- **Focus ring:** Interactive controls use `focus-visible:ring-3 focus-visible:ring-ring/50` or the existing shadcn equivalent.

### Named Rules
**The Flat-By-Default Rule.** Do not pair a 1px border with a broad decorative shadow. If a surface needs separation, use border, ring, tonal fill, or layout spacing.

## 5. Components

### Buttons
- **Shape:** Rounded-lg, approximately 8px.
- **Primary:** Workbench Ink background with Canvas White text; reserve for the next meaningful action.
- **Hover / Focus:** Existing shadcn transitions and focus-visible rings. Never remove keyboard focus.
- **Secondary / Ghost / Outline:** Used for reversible, navigational, or lower-risk actions. Outline buttons should not outnumber primary decisions in a high-stakes action cluster without grouping.

### Chips
- **Style:** Badges use pill geometry, compact text, and token variants (`default`, `secondary`, `outline`, `destructive`).
- **State:** Status badges must include readable status text. Do not use color-only chips for pass/fail or market direction.

### Cards / Containers
- **Corner Style:** 12px (`rounded-xl`) for cards, 8px (`rounded-md`) for nested operational blocks.
- **Background:** `bg-card` for major panels, `bg-muted/20` or `bg-background/60` for compact sub-panels.
- **Shadow Strategy:** No broad decorative shadow; use border/ring separation.
- **Border:** `border` or `ring-1 ring-foreground/10`.
- **Internal Padding:** 16px default card spacing, 12px compact card spacing.

### Inputs / Fields
- **Style:** 40px height, 8px radius, token border and background.
- **Focus:** Visible token ring via shared input/button primitives.
- **Error / Disabled:** Use destructive token plus explanatory text; disabled controls must keep enough contrast to reveal why a step is blocked nearby.

### Navigation
- **Style:** Familiar side/top navigation, lucide icons, active state through fill/foreground change, and persistent page labels.
- **Mobile treatment:** Collapse structure rather than shrinking typography. Touch targets should remain at least 44px where mobile use is expected.

### Strategy Lab
- **Style:** Dense three-column expert workbench on wide screens, stacked sections on narrow screens.
- **Paper Review:** High-stakes controls must show paper-only scope, current intent status, risk decision, and next allowed action before any submit control.

## 6. Do's and Don'ts

### Do:
- **Do** use shared shadcn/Tailwind components before introducing new primitives.
- **Do** keep paper-only boundaries visible in candidate, review, approval, submit, and audit states.
- **Do** pair market/risk colors with text labels and icons.
- **Do** use `bg-muted/20`, borders, and spacing for structure rather than decorative shadows.
- **Do** keep tables dense but scannable with clear header labels and stable action columns.

### Don't:
- **Don't** make this feel like a public trading app, broker execution console, live-order ticket, or promotional SaaS dashboard.
- **Don't** introduce UI language that suggests live trading, broker credentials, automatic execution, or paper-to-live promotion.
- **Don't** use fake static dashboard data to make screens feel richer.
- **Don't** use gradient text, decorative glassmorphism, broad ghost-card shadows, side-stripe card accents, or oversized rounded cards.
- **Don't** rely on red/green alone for market direction, RiskGuard, approval, rejection, or error states.
