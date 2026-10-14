# GitHub Pages and contributor Archify implementation plan

> Scope revised after user direction: GitHub Pages introduces the project to users; Archify remains contributor-only. This plan replaces the earlier public-architecture-page design.

**Goal:** Publish bilingual project introduction, features, usage guidance, and truthful download/build links at `https://dt418.github.io/evkey-linux-community/`.

**Architecture:** `site/` contains only the two end-user pages and shared CSS. Four source-backed Archify diagrams, candidates, and generated HTML stay under `.archify/`. Normal Check CI verifies Archify provenance; Pages deploys only `site/`.

**Stack:** Static HTML/CSS, pinned local Archify v3.0.1 for contributor diagrams, Python standard library checker/tests, GitHub Pages Actions. No web framework, host-page JavaScript, or Archify build step in Pages deployment.

**Spec:** `docs/superpowers/specs/2026-10-05-github-pages-archify-design.md`

## Global constraints

- Public identity: independent EVKey-inspired Fcitx5/Lotus/Bamboo community edition; not official, affiliated with, endorsed, or distributed by EVKey's author.
- GitHub Releases API was empty at review. Link the source ZIP and Releases page; do not claim binary packages exist.
- Do not promise universal application compatibility, error-free focus races, or unconditional fallback. Smooth/Uinput is optional; helper package installation and service enablement are separate. Helper handles bounded edit-key requests, not composed text or raw keyboard input.
- Public routes: `/evkey-linux-community/` and `/evkey-linux-community/en/`. Correct canonical URLs, reciprocal `hreflang`, document language, and prefix-safe local links.
- No public architecture routes, Archify links, diagram embeds, or generated diagram copies.
- Pin Archify `tt-a1i/archify` v3.0.1 to `2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c`; archive SHA-256 `b0b23bd28db314f04ca8ab9620fe20f8c1ac6474a3546bd8fe4679508aa1b7f5`.
- Diagram evidence pins project source commit `87e6de6e59b96310876450a723e3b9ce5d613d41`; behavior changes require human re-tracing.
- Diagram candidates and outputs stay under `.archify/`; manifest is `.archify/diagram-manifest.json`, checksum inventory `.archify/SHA256SUMS`.
- Pages artifact contains `site/` only. Its deploy job does not install Node, Archify, Chrome, or check out source.
- Do not enable Pages or publish before local real-browser acceptance.
- No native engine behavior changes; do not run native harness solely for this work.

## Task 1: Pin Archify project skill — completed

The project-local pinned CLI, mirrored skill, license, attribution, and lock record are committed. Preserve exact upstream skill contents and pin.

## Task 2: Generate and verify contributor-only diagrams

**Files:** `.archify/` candidates/generated HTML, `.archify/diagram-manifest.json`, `.archify/SHA256SUMS`, `tools/regenerate_archify_diagrams.py`, `tools/check_archify_artifacts.py`, `test/test_archify_artifacts.py`.

**Contract:** Four exact type/locale pairs: runtime architecture and input-mode workflow, each English and Vietnamese. Manifest rows contain candidate/generated paths and their hashes; no public/published field. Checker rejects path traversal, missing/modified artifacts, incorrect provenance, and site-publication fields. Regenerator runs pinned finalizer gates and updates only `.archify/` files.

**Completed:** Candidates and generated HTML are source-backed, Vietnamese translations are reviewed, and pinned finalizer validation/provenance/browser gates passed. Integration must rerun focused unit tests and checker after final changes. Do not rerun finalizer unless candidate/source evidence changes; browser receipts can contain workstation-specific data and are not committed.

## Task 3: Build bilingual end-user pages

**Files:** `site/index.html`, `site/en/index.html`, `site/assets/site.css`; root README links only if needed.

- Present project identity, supported input methods and charsets, Fcitx5 usage, mode tradeoffs, build instructions, source ZIP, and Releases page.
- State clearly that no prebuilt packages are available at review; link source archive and README build instructions.
- Use the existing editorial visual language and fonts with Vietnamese glyph coverage. Keep keyboard focus visible, links ordinary, and layout usable at 320px.
- Add only two public routes. Remove architecture pages, diagram copies, diagram manifest aliases, and diagram-only public styles.
- Browser-check both routes under `/evkey-linux-community/`; verify language switch, local anchors, canonical/hreflang, focus, responsive layout, no horizontal overflow, and real download/build destinations. Confirm no Archify link or diagram request.

## Task 4: Pages workflow and maintainer documentation

**Files:** `.github/workflows/pages.yml`, `.github/workflows/check.yml`, `docs/development.md`.

- Pages workflow has empty default permissions, package `contents: read`, and separate deploy permissions limited to `pages: write` and `id-token: write`. Deploy uses `github-pages`, depends on packaging, checks out no repository content, and serializes without cancelling an active deployment.
- Trigger Pages only for `main` changes under `site/**` or its own workflow; manual dispatch is main-only. Upload only `site/`; do not run Archify or its checker in Pages packaging.
- Normal Check workflow runs Archify artifact checker and focused tests while preserving existing checks and triggers.
- Document pinned CLI/source evidence, contributor-only output locations, Node/Chrome requirements, shell-local browser configuration, regeneration commands, font/network behavior, and manual review. Do not document machine-specific executable paths.

## Task 5: Acceptance, enable Pages, publish, verify

1. Run `python -m unittest discover -s test -p 'test_archify_artifacts.py' -v` and `python tools/check_archify_artifacts.py --root .`; inspect exact output and ensure no site artifact includes `.archify/`.
2. Serve `site/` at `/evkey-linux-community/`. Use a real Chrome browser to inspect both localized pages at desktop and 320px widths; test links, focus, language switch, anchors, and page overflow. Open the source ZIP and build/Release destinations; record observed status/output only. Do not enable Pages before this passes.
3. Re-read GitHub Pages API state. If absent, create workflow publishing with authorized repository settings access; if present, preserve its current configuration. Do not claim setting changes without observed API output.
4. Reconcile reviewed work with current `main`, preserve unrelated user changes, push only after local acceptance and Pages workflow setup, and wait for Check and Pages workflows. Fix actual failures.
5. Visit live Vietnamese and English routes in Chrome. Verify rendered content, language links, source/build destinations, no public Archify pages/content, and successful workflow deployment. Report only observed live output.

## Integration and delivery

Run tests/checker and browser acceptance after all edits are integrated. Review workflow permissions, triggers, and artifact path; confirm Pages artifact contains only user-facing site files. Commit scoped changes and deploy only after acceptance. Keep Linux-native compatibility claims separate from website acceptance.
