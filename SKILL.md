# Open-Booth Design Skill

Open-Booth is the **browser-based recording surface** of the content-systems family. The product's identity is **podcast recording with a vibe of your choice** — a deliberate skin system: terminal-aesthetic default plus eight named skins (`studio-warm`, `clean-light`, `soft-dark`, `broadcast`, `analog`, `glass`, `campfire`, `newsroom`). Switch via `?skin=<name>` URL param.

## Ground Rules

**This is a non-pairing surface in a non-pairing family.** Skins do not pair with each other — they're alternatives, not siblings. Don't try to converge them.

**Tokens live per-skin** in `client/skins.css` as `:root[data-skin="<name>"]` blocks. The base recorder CSS handles the default terminal aesthetic.

**Required per skin:** `--bg`, `--surface`, `--border`, `--accent`, `--on-accent`, `--text`, `--text-dim`, `--radius`, `--radius-sm`, font stack. Missing any → skin doesn't ship.

**Family-level rules apply to every skin:**
- Body / UI ≥ 14px proportional (or ≥ 13px monospace for mono skins)
- Tracked uppercase labels ≥ 12px on control surfaces
- No `#000000` text, no `#ffffff` background unless the skin's concept genuinely demands it (`clean-light` is the only skin that uses near-white)
- Tabular-nums on any numeric column
- No body below 14px proportional, anywhere

## Adding a new skin

1. Metaphor name (one word or hyphen-joined) describing the production register
2. New `:root[data-skin="<name>"]` block in `client/skins.css` with every required token
3. Verify against every component in the recorder surface — no half-styled skins
4. Test legibility at 1080p compression (the surface is sometimes screen-recorded)
5. Document name + one-line description in DESIGN.md `skins:` frontmatter

## Pairs With

None. Open-Booth is non-pairing; siblings (chassis, private-booth, transcriber) are also non-pairing within the content-systems family.

## Never Do

- Half-style a skin — every skin is complete or it doesn't ship
- Mix skin tokens — switching `?skin=foo` is a complete swap, never a partial blend
- Add a skin without a clear production-register metaphor — vibe must be nameable
- Use family chrome from siblings (chassis indigo, private-booth electric yellow) in a new Open-Booth skin
- Ship a skin that violates the family legibility floor — escalate or fix
- Ship a skin that uses pure black `#000000` text or pure white `#ffffff` background (except `clean-light` for backgrounds, which is the deliberate exception)

---

Full system in `DESIGN.md` (this repo root). Live tokens at `client/skins.css`. Family rules at `../content-systems/design/BRAND.md`. Cross-product handoff bundle at `../content-systems/design/handoff/`.
