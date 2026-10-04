# GitHub Pages and Archify design

Status: design approved for specification. This document defines the public project site and publishing contract; it is not implementation approval. The user must review this spec before an implementation plan is created, then approve that plan separately before code changes.

## Goal

Publish a bilingual, public project site for EVKey Linux Community and use Archify to explain source-backed runtime architecture and input-mode behavior. Keep the native Fcitx5 product independent of the website. Deploy only reviewed, static site artifacts through GitHub Pages.

## Audience and product truth

- Vietnamese Linux users seeking a clear feature overview and source-build instructions.
- English-speaking contributors seeking module ownership, mode behavior, and the optional helper's security boundary.
- The project is an independent community edition inspired by EVKey, based on Fcitx5 Lotus and Bamboo. It is not the official EVKey release and is not affiliated with or endorsed by EVKey's author.
- The public Releases API is currently empty. Do not show a download-package CTA or imply that binaries are published. Link users to the build instructions and source repository.
- Describe source behavior, not universal application compatibility. Smooth/Uinput is optional; installing its package and enabling its service are distinct actions. Its helper processes bounded edit-key requests rather than composed text or raw keyboard input. Fallback is conditional; interrupted replacement must not be described as blindly retried or universally safe.

## Information architecture and URL contract

Use a small static site rooted at `site/`:

| Page | Source path | Public URL |
| --- | --- | --- |
| Vietnamese landing | `site/index.html` | `https://dt418.github.io/evkey-linux-community/` |
| English landing | `site/en/index.html` | `https://dt418.github.io/evkey-linux-community/en/` |
| Vietnamese architecture | `site/architecture/index.html` | `https://dt418.github.io/evkey-linux-community/architecture/` |
| English architecture | `site/en/architecture/index.html` | `https://dt418.github.io/evkey-linux-community/en/architecture/` |

Landing pages explain the product, the user-documented input modes, source-build instructions, and non-affiliation notice, with links to the matching architecture page, source repository, and contribution docs. Each architecture page presents two interactive Archify views—runtime/module architecture and input-mode/fallback workflow—with a readable text equivalent, source links, and a direct-open link for each diagram. Every page links to the corresponding page in the other language.

Navigation, stylesheet and image references, iframe sources, and language-switch links use relative URLs and resolve beneath `/evkey-linux-community/`; never use origin-root URLs such as `/assets/site.css`. Each page has an absolute `rel="canonical"` URL and `hreflang` alternates for the reciprocal Vietnamese/English route, each including the full project-site prefix. Use `lang="vi"` and `lang="en"` on the corresponding documents and localized Viewer interfaces.

## Visual and interaction direction

Create an editorial engineer's field guide, not a generic software landing template: warm paper surface, ink-dark text, deep teal, and one controlled signal accent; strong display/body hierarchy with restrained monospace for technical labels. Keep clear spacing, visible focus, strong contrast, responsive cards, and legible code references. Do not load fonts, scripts, analytics, or other assets from external services. Site navigation and language switching use ordinary links; no host-page JavaScript is required.

Embed each self-contained Archify document in a titled, lazy-loaded frame and provide a visible direct-open link. Provide a readable semantic text equivalent outside the frame; do not treat the generated SVG/HTML as the only way to understand a diagram. Verify iframe behavior, accessible names, keyboard use, narrow layouts, and zoom separately from Archify's own browser check. Do not promise that Archify viewer interaction is optimized for mobile; on small screens, the text equivalent and direct-open link remain usable.

## Archify artifacts, evidence, and updates

Pin upstream `tt-a1i/archify` v3.0.1 to commit `2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c`. Verify the official release archive SHA-256 `b0b23bd28db314f04ca8ab9620fe20f8c1ac6474a3546bd8fe4679508aa1b7f5`. Retain the MIT license, source notice, skills-lock entry, and exact project-local `.agents/skills/archify` / `.claude/skills/archify` mirror. Do not include upstream website/gallery/release bundle or `node_modules` in the Pages artifact.

Keep one editable JSON candidate for each diagram/locale under its own timestamped `.archify/<type>-<slug>-<timestamp>/` folder, as required by the upstream skill. `meta.output` writes a standalone HTML beside its candidate; copy that output byte-for-byte into the matching site path: `site/diagrams/vi/runtime-architecture.html`, `site/diagrams/vi/input-modes.html`, `site/diagrams/en/runtime-architecture.html`, and `site/diagrams/en/input-modes.html`. Vietnamese artifacts set `meta.locale` to `vi` and include a reviewed, complete `meta.translations` catalog with exact placeholder tokens; English artifacts set `meta.locale` to `en`. No machine-translated or incomplete catalogs.

Each candidate pins the credential-free repository origin and complete 40-character project source revision used for its evidence. Initial source snapshot: `87e6de6e59b96310876450a723e3b9ce5d613d41`. `.archify/SHA256SUMS` records source candidate and generated-artifact hashes; `site/diagrams/SHA256SUMS` records public HTML hashes. Show the source snapshot commit on both localized architecture pages and use links to that commit, not moving `main` links. A relevant source behavior change requires a human to retrace affected behavior, revise its candidate/evidence, regenerate all affected localized outputs, refresh both manifests, and review the diff together. Deployment never silently presents old diagrams as current source.

The runtime diagram may show only observed boundaries and relationships: application/Fcitx5/add-on/Bamboo integration; Settings-to-Fcitx Controller over the session bus; the optional helper path for editing-key requests; `/dev/uinput` output; peer-UID and active/local/unlocked session checks. The workflow diagram distinguishes Preedit, Fake Backspace, and Smooth/Uinput, including conditions and fallback behavior. Cite paths/line ranges from the pinned commit. Do not conflate Settings D-Bus with helper AF_UNIX transport, imply composed text is sent to the helper, claim the helper reads raw keyboard input, or turn source checks into a promise of compatibility or race-free execution.

The pinned upstream CLI requires Node >=18. Its `finalize` gate checks/validates standalone diagrams and runs a real desktop-browser check; it does not check the hosting site's navigation, accessibility, embed layout, repo-prefix routes, or mobile text alternatives. For each of the four generated HTML files, inspect network activity and ensure the initial document makes no external requests; visitor-triggered source/repository links are allowed. `docs/development.md` records the exact pinned source/digest, all candidate and output paths and hashes, regeneration commands, required Chrome/Chromium, manifests, evidence snapshot rule, and manual review/update procedure.

## GitHub Pages publishing

Create `.github/workflows/pages.yml` as a dedicated custom workflow. Upload only the checked-in `site/` directory as the Pages artifact. Do not deploy repository root or the existing `docs/` development material. The production deploy path consumes prebuilt HTML and installs neither Archify, Node, nor Chrome.

Trigger on pushes to `main` affecting `.archify/**`, `site/**`, or the publishing workflow; allow `workflow_dispatch`, but deploy only from `main`. No pull-request deployments.
- Default workflow permissions are empty. The package job receives `contents: read` only. A separate deploy job receives only `pages: write` and `id-token: write`, needs the package job, uses the `github-pages` environment, and does not check out repository content.
- Serialize Pages deployment without cancelling an in-progress public deployment.
- The package job checks `.archify/SHA256SUMS` and `site/diagrams/SHA256SUMS`, then byte-compares each generated `.archify` HTML with its checked-in site copy before upload.
- Do not enable Pages or initiate the first public deployment until local site and diagram acceptance passes. Then create the Pages site with workflow publishing (`POST /repos/dt418/evkey-linux-community/pages`, body `{"build_type":"workflow"}`) and push the ready site/workflow. If the authenticated account lacks Pages settings authority, stop before pretending deployment is enabled.
- After the first deployment, verify the live four routes, language links, iframe/direct diagram routes, and served hashes; browser-check actual rendered surfaces.

## Acceptance

1. All four pages render in Vietnamese/English, with correct reciprocal language route, canonical route, document language, source links, no origin-root asset URLs, no broken internal links, and no unsupported downloads claim.
2. All four Archify candidates pass the pinned `finalize` gates against their pinned project revision; exact generated bytes match the recorded checksum manifest.
3. Site host acceptance is separate: serve the site under `/evkey-linux-community/`; visit all routes at desktop and narrow viewport; test keyboard navigation and visible focus, language switch, iframe title, text equivalent at narrow width and 200% zoom, direct-open links, and no horizontal page overflow. Inspect browser network requests for all four diagrams.
4. Before Pages settings change, inspect the local site in a real browser and correct defects. After deployment, revisit the public URL and verify route behavior and that served diagram bytes match the committed manifest.
5. Update `README.md` and `README.en.md` with the canonical site link, `docs/development.md` with authoring/regeneration instructions, and third-party source/license/lock records for Archify.
6. GitHub Pages workflow succeeds on `main`; repository Pages settings use GitHub Actions workflow publishing; report actual public URL and workflow run evidence.

## Non-goals

No web framework or content-management system; no release/package publishing; no application downloads; no runtime service or API; no analytics, telemetry, external font/CDN dependency, third-party forms, or automated claims inferred from code; no automatic regeneration that reuses stale semantic diagrams after source changes.

## Approval boundary

This spec records the reviewed design only. The next step is a separate implementation-plan artifact for user review. No website, diagram, workflow, repository setting, or product code implementation is authorized until the user approves that plan.