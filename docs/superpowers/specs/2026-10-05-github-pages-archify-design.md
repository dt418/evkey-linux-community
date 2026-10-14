# GitHub Pages and contributor Archify design

Status: revised after user direction. GitHub Pages is a bilingual end-user project site; Archify diagrams are contributor-only repository references and must not be published or linked from Pages.

## Goal

Publish a bilingual project introduction, feature overview, usage guide, and truthful download links for EVKey Linux Community. Keep native Fcitx5 product behavior independent of the static site. Deploy only reviewed files from `site/` through GitHub Pages.

## Audience and product truth

- Vietnamese and English Linux users seeking project information, feature descriptions, usage guidance, and download/build options.
- The project is an independent community edition inspired by EVKey, based on Fcitx5 Lotus and Bamboo. It is not the official EVKey release and is not affiliated with, endorsed, or distributed by EVKey's author.
- The GitHub Releases API was empty at review. Do not imply binary packages are available. Link to the source ZIP and Releases page; state that users must build from source until packages are published.
- Describe supported behavior without promising universal application compatibility. Smooth/Uinput is optional; installing its package and enabling its service are distinct actions. Its helper processes bounded edit-key requests, not composed text or raw keyboard input. Fallback is conditional; interrupted replacement must not be described as blindly retried or universally safe.

## Public information architecture

The static site is rooted at `site/`:

| Page | Source path | Public URL |
| --- | --- | --- |
| Vietnamese home | `site/index.html` | `https://dt418.github.io/evkey-linux-community/` |
| English home | `site/en/index.html` | `https://dt418.github.io/evkey-linux-community/en/` |

Each page covers project identity, input methods and output charsets, practical Fcitx5 usage, input-mode tradeoffs, and download/build choices. Navigation is limited to features, usage, downloads, and language switching. Do not add public architecture routes, Archify links, diagram embeds, or diagram copies. Use relative in-site URLs beneath `/evkey-linux-community/`, absolute canonical URLs, reciprocal `hreflang`, and accurate `lang` attributes.

## Visual and interaction direction

Use the existing editorial field-guide style: warm paper, ink-dark text, deep teal, one signal accent, clear hierarchy, visible focus, responsive layout, and readable code examples. Use system fonts with Vietnamese glyph coverage; no external font, script, analytics, or other asset dependency. No host-page JavaScript. Links remain ordinary keyboard-accessible anchors.

## Contributor-only Archify artifacts

Pin `tt-a1i/archify` v3.0.1 to commit `2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c`; retain its MIT license, source notice, skill lock, and project-local mirrors. Keep four reviewed candidates and generated HTML under `.archify/`, with source evidence pinned to `87e6de6e59b96310876450a723e3b9ce5d613d41`. `.archify/diagram-manifest.json` maps candidate and generated paths and their hashes; `.archify/SHA256SUMS` inventories both. No diagram artifact is copied into `site/`.

The contributor references cover runtime architecture and input-mode/fallback workflow in English and Vietnamese. Vietnamese translations must be manually reviewed, complete, and preserve exact placeholder tokens. Their bundled JetBrains Mono subset includes Vietnamese glyphs; viewer text uses local/system font fallback. Initial diagram loads must make no external requests.

A Python standard-library checker and focused unit tests verify the manifest, exact locale/type pairs, pinned provenance, containment, file hashes, and checksum inventory. A local regenerator invokes the pinned Archify `finalize` gates and refreshes only `.archify/` outputs. Node and Chrome/Chromium are local contributor prerequisites; browser executable configuration stays in the current command/environment and is never checked in.

## GitHub Pages publishing

Use a dedicated `.github/workflows/pages.yml`. Upload only `site/`; do not deploy repository root, `.archify/`, or development docs. The Pages workflow triggers on `main` changes under `site/**` or to its own workflow, and supports manual dispatch only for `main`. The normal Check workflow validates contributor Archify provenance and runs its focused tests. Pages packaging does not run Archify, Node, or Chrome.

- Default workflow permissions are empty. The package job receives `contents: read`; the separate deploy job receives only `pages: write` and `id-token: write`, uses the `github-pages` environment, depends on packaging, and does not check out source.
- Serialize deployments without cancelling an in-progress public deployment.
- Do not enable Pages or initiate first deployment until local end-user pages pass real-browser acceptance. Then configure workflow publishing and push the reviewed implementation. If account permissions are insufficient, report the exact required settings action; do not claim deployment succeeded.
- After deployment, verify both localized routes, language switching, source/build links, served content, and absence of public Archify material.

## Acceptance

1. Both localized pages render under `/evkey-linux-community/`; each has correct document language, canonical URL, reciprocal language link, user-facing features/usage/download information, and no Archify or architecture links.
2. The source ZIP, README build instructions, and Releases links resolve to the intended GitHub destinations. No binary package availability is claimed unless verified.
3. The public site works at desktop and 320px/narrow widths, has no horizontal page overflow, visible keyboard focus, usable language switching, and working local navigation. Inspect real-browser output and network requests.
4. All four contributor diagrams pass the pinned `finalize` gates and the manifest/checksum tests. Their generated HTML remains under `.archify/` and outside Pages artifacts.
5. Pages is enabled only after local browser acceptance. After publication, verify the live Vietnamese and English routes and confirm Pages contains no architecture pages, diagram copies, or Archify links.
6. Update `docs/development.md` with contributor regeneration/review instructions and preserve the existing native development and hardware-evidence guidance.

## Non-goals

No web framework or CMS; no release/package publishing; no binary download claim; no runtime service/API; no analytics, telemetry, external font/CDN dependency, third-party forms, or automatic diagram regeneration that reuses stale source evidence. Archify is not part of the public product site.

## Approval boundary

This revision records the user's corrected scope. Implementation and deployment remain subject to local acceptance, least-privilege workflow checks, and verification of live output.
