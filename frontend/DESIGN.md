# Design system notes

## Palette

| Token | Hex | Use |
|---|---|---|
| `graphite-950/900/800/700/600` | `#17171b` → `#46464f` | Dark chrome: title bar, search well, people rail |
| `paper-50/100/200/300` | `#f8f5ee` → `#d9cdb8` | Warm content surfaces: cards, main background |
| `ink-900/700/500` | `#262420` → `#726c5f` | Text on paper |
| `steel-300/400/500` | `#c2c4cb` → `#74767f` | Text/icons on dark chrome |
| `gold-400/500/600` | `#d9b64a` → `#a9841c` | The **one** accent — reserved for selection state and primary actions |

The brief's reference points (Lightroom, Capture One, older Apple
Photos, macOS pro apps) all share one structural idea: dark anodized
chrome housing the tool, warm/light surfaces housing the content. That
split does double duty here — it's also what makes the single gold
accent effective. If everything were colorful, gold selection
wouldn't read as special.

## Why brushed-graphite chrome + warm paper content

Flat, single-hue UIs read as "web app." Real desktop photography tools
almost always separate **chrome** (the tool itself — toolbars, rails,
panels) from **content** (the work — photos, prints, contact sheets),
and render them with different material logic. `.chrome-surface` is a
very subtle vertical gradient + a 1px top highlight, meant to suggest
anodized aluminum, not a colorful background. `.paper-surface` and
`.well-surface` do the same for the two content-adjacent textures:
paper cards sit slightly raised (`shadow-card`), while the search bar
and people rail sit recessed (`shadow-inset-well`) — tactile opposites,
on purpose, so pressing "into" the search well vs. picking "up" a
person card feel like different physical actions.

## Where the gold goes (and where it doesn't)

Per the brief: selection gets a gold border, soft shadow, and slight
elevation — see `PersonCard`. Chips reuse the same gold, since a chip
*is* a visual echo of "this person is selected." Buttons only use gold
for the single primary action per view (`Export`) — every other button
is a neutral "chrome" or "subtle paper" key. Restraint is what keeps
gold meaning something.

## Motion

Framer Motion is used only for physically-plausible micro-motion: a
card lifting a few pixels on hover/select, a chip scaling in/out, a
modal settling into place. Nothing spins, bounces, or slides in from
off-screen — the brief asked for "subtle," and the test for every
animation here was "would a real photograph or printed card move this
way if nudged?"

## Typography

Inter only, per the brief — hierarchy comes entirely from size/weight
(600–700 for names and headings, 500 for labels/buttons, 400 for body),
not from a second typeface. Self-hosted via `@fontsource/inter` rather
than `next/font/google`, since this is meant to become an **offline**
desktop app — it can't depend on a network fetch to Google's font CDN
at build time or runtime.

## Known gap: ESLint

`npm run lint` currently crashes with a circular-JSON error inside
`eslint-config-next`'s compatibility shim against this environment's
ESLint 9.39.5 — a version-compatibility issue in the tooling chain
itself, not in this project's source. `npm run build` (which includes
full TypeScript type-checking via Next's Turbopack build) passes
cleanly and is the authoritative correctness check for this codebase.
