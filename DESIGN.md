---
name: Open-Booth · Recording Surface
description: Browser-based podcast recording surface with skin system — terminal default plus eight named skins for varying production aesthetics
version: 1.0.0
updated: 2026-05-01
pairs-with: none
family-brand: ../content-systems/design/BRAND.md
tokens-css: client/skins.css   # the skin token system; per-skin :root[data-skin="..."] overrides

skin-system: true   # this product is intentionally skinnable; see SKILL.md

skins:
  default:        terminal aesthetic (no data-skin attribute) — mono typeface, dark grounds, monospace status
  studio-warm:    warm production-studio palette
  clean-light:    bright daylight surface, the only light skin
  soft-dark:      muted dark, lower contrast
  broadcast:      classic broadcast register
  analog:         vintage warmth
  glass:          translucent, layered
  campfire:       deep warm, intimate
  newsroom:       editorial, considered
---

# Open-Booth Design System

## Brand Identity

Open-Booth is a **browser-based recording surface** with a deliberate **skin system** — the product's identity *is* "podcast recording with a vibe of your choice." Each skin is internally consistent; the running app picks one via `?skin=<name>` URL param.

This is unusual within the content-systems family. chassis, private-booth, transcriber each have a single visual register; Open-Booth has nine (default + 8 named). That's by design — each skin serves a different recording context (warm studio for cosy podcasts, broadcast for newsy interviews, glass for premium production, campfire for intimate fireside chats).

Per content-systems' BRAND.md, Open-Booth does not pair-check against siblings. Skins do not pair-check against each other either — they're alternatives, not siblings.

What we're avoiding:
- Trying to converge skins into a single "Open-Booth look" — defeats the point
- Half-styling new skins — every skin must be complete or it doesn't ship
- Letting the URL param leak default tokens into a named skin

---

## Platform Context

- **Platform:** browser-only static recording surface. Used during live recording sessions; participants and host both run it.
- **Implications:** the surface frequently appears in screen recordings of the recording session itself (a host's monitor, occasionally publishable as BTS content). Each skin must hold up at 1080p compression.
- **Pace:** session-length per visit (typically 20–90 minutes). Density secondary to clarity — participants need to see recording state at a glance.

---

## Legibility Floor

Family floor (body / UI ≥ 14px proportional, or ≥ 13px monospace for skins that use mono; labels ≥ 12px on control surfaces) applies to **every skin**. A skin that violates the floor doesn't ship — even if the visual concept demands tight type.

If a skin's design intent demands sub-floor sizing for a specific element (e.g. tracked uppercase status labels in the broadcast skin), document the divergence inline in `skins.css` as a comment with rationale, and surface it on the next family-level audit.

---

## Pairs With

**None — and skins do not pair with each other.** Open-Booth is a non-pairing surface in a non-pairing family. Each skin is a standalone visual register; switching skins is a complete swap, not a partial blend.

Family rules at [`../content-systems/design/BRAND.md`](../content-systems/design/BRAND.md).

---

## The Skin System

### How skins work

The base `client/skins.css` contains:

1. **Shared structural overrides** — layout, radii, button shapes that survive across skins (these are minor; most surfaces are skin-driven).
2. **One `:root[data-skin="<name>"]` block per named skin** declaring that skin's tokens — surface, accent, surface-on-accent, border, font stacks, radius.

The default (no `data-skin` attribute) uses the terminal aesthetic baked into the base recorder CSS. Adding `?skin=studio-warm` to the URL flips the body's `data-skin` attribute and the skin's tokens take over.

### Required tokens per skin

Every skin must declare:

- `--bg`, `--surface`, `--bg-sidebar` (or equivalent)
- `--border`
- `--accent`, `--on-accent` (text colour on accent fills)
- `--text`, `--text-dim`
- `--radius`, `--radius-sm`
- Font stack tokens (`--font` or per-role tokens if the skin uses multiple)

Missing any of these = skin is incomplete = doesn't ship.

### Adding a new skin

1. Pick a metaphor name (one word or hyphen-joined) describing the production register the skin serves (`studio-warm`, `broadcast`, `campfire`).
2. Add a `:root[data-skin="<name>"]` block to `client/skins.css` declaring all required tokens.
3. Visually verify against every component in the recorder surface — no half-styled skins.
4. Test legibility at 1080p compression (the surface is screen-recorded sometimes).
5. Document the skin name and one-line description in this DESIGN.md's `skins:` frontmatter map.

### Removing a skin

Open question — no skin has been removed yet. If one needs to go, leave the token block in `skins.css` for one release with a `@deprecated` comment, then remove. Don't break inbound URLs immediately.

---

## Available skins

| Skin name | Register |
| --------- | -------- |
| (default) | Terminal aesthetic — mono typeface, dark grounds, monospace status |
| `studio-warm` | Warm production-studio palette |
| `clean-light` | Bright daylight; the only light-grounded skin |
| `soft-dark` | Muted dark, lower contrast than default terminal |
| `broadcast` | Classic broadcast register |
| `analog` | Vintage warmth |
| `glass` | Translucent, layered |
| `campfire` | Deep warm, intimate |
| `newsroom` | Editorial, considered |

Visual specifics per skin live in `client/skins.css` — the tokens are the source of truth, not this README. Don't try to re-document them here; they'll drift.

---

## Component Patterns (skin-agnostic)

The recorder surface has a fixed set of components that every skin styles via tokens:

- **Video pane** (`.video-wrap`) — the participant's preview
- **Name gate** (`#nameGate`) — landing form before recording
- **Recording panel** (`.r-panel`) — record/stop controls + status
- **Strip** (`.s-strip`) — bottom strip with chapter markers
- **Log wrap** (`.log-wrap`) — recording log/transcript
- **Notice** — system messages
- **Host controls** — host-only buttons
- **Controlled strip** — the host's view of participant strips

These components are constant. Skins change *how* they look, not *what* they are.

---

## Spacing

Skin-controlled. Each skin's `--radius` and any internal padding tokens drive layout. Common increments stay close to 4 / 8 / 12 / 16 / 20 / 24 px to stay aligned with the family.

---

## Generates

When asked to scaffold or extend:

- `client/skins.css` — live tokens for every skin, single source of truth
- `client/recorder.html` and supporting JS — the surface itself (skins are CSS-only; the markup is constant)
- Per-skin token blocks must be complete (every required token declared)
- `SKILL.md` (repo root) — compressed brief
- Family handoff bundle at `../content-systems/design/handoff/`

For new skins, a concept HTML showing the named skin against the standard surface is the deliverable. Skin proposals go in `design/concepts/<skin-name>.html`.

---

## Surface Map

```
DESIGN.md                            ← canonical spec (this file)
SKILL.md                             ← compressed brief
client/skins.css                     ← live tokens for every skin
client/                              ← recorder surface (HTML, JS, supporting CSS)
design/concepts/                     ← skin proposals (when authored)
```

Family layer:

```
../content-systems/design/BRAND.md   ← universal rules
../content-systems/design/handoff/   ← cross-product handoff bundle
```
