# GitHub Pages with Archify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task with a fresh reviewer gate after each task. Use project-local skills; keep main session as integration owner. All subagents skip builds, tests, lint, and formatters mid-flight. Run gates once at integration checkpoints.

**Goal:** Publish a source-accurate bilingual static project site at GitHub Pages with four localized, interactive Archify diagrams.

**Architecture:** Keep authored HTML/CSS in `site/` and embed the checked-in standalone Archify artifacts from `site/diagrams/`. Keep editable candidates and source provenance in `.archify/`; validate candidates, generated outputs, and published copies before uploading only `site/` through a split least-privilege Pages workflow.

**Tech Stack:** HTML5, CSS, Node.js >=18 and pinned Archify v3.0.1 for local diagram generation, Python 3 standard library for manifest verification, GitHub Pages Actions. No website framework, host-page JavaScript, or build dependency in the Pages deploy job.

**Spec:** `docs/superpowers/specs/2026-10-05-github-pages-archify-design.md`

## Global Constraints

- Public identity: independent EVKey-inspired Fcitx5/Lotus/Bamboo community edition; not official or endorsed by EVKey's author.
- Do not promise universal input-method compatibility, error-free focus races, or published binary downloads.
- Settings communicates with Fcitx Controller over session D-Bus; helper edit requests use AF_UNIX; composed text is committed through Fcitx, not sent to helper.
- Smooth/Uinput is optional; installing its package and enabling its service are separate; fallback is conditional and interrupted replacement is not blindly replayed.
- Base URL is `https://dt418.github.io/evkey-linux-community/`; navigational/assets/iframe URLs are relative, canonical and language-alternate URLs include the project prefix.
- Archify source is `tt-a1i/archify` v3.0.1 at `2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c`; verified release-archive SHA-256 is `b0b23bd28db314f04ca8ab9620fe20f8c1ac6474a3546bd8fe4679508aa1b7f5`.
- Diagram evidence pins project source commit `87e6de6e59b96310876450a723e3b9ce5d613d41`; relevant source changes require human re-tracing and regeneration.
- The Vietnamese Archify Viewer uses `meta.locale: "vi"` and complete reviewed `meta.translations`; English uses `meta.locale: "en"`.
- Pages artifact includes `site/` only. Pages deployment job does not install Node, Archify, or Chrome.
- No Pages repository-setting mutation or public deployment before successful local diagram and host-page browser acceptance.
- Use `tools/dev.sh` only if native project behavior changes; this plan changes no native engine behavior.

## Review Focus

1. **Project-prefix routing:** nested routes, assets, canonical links, diagram frames, and reciprocal language links resolve below `/evkey-linux-community/`. Task 3 browser-checks all four routes under that prefix.
2. **Locale parity:** document language, bilingual page copy, Archify Viewer locale, and reciprocal same-page toggles agree. Tasks 2–3 finalize both locales and exercise each switch.
3. **Diagram semantics/provenance:** helper operation, fallback conditions, and mode distinctions match pinned source; generated outputs, candidates, and published copies are byte-verified. Task 2 tests mismatch/path failures and finalizes all four artifacts; its fresh reviewer checks each source assertion.
4. **Accessible host page:** iframe names, text equivalents, keyboard focus, narrow viewport/200% zoom, and direct-open links remain usable without relying on mobile diagram interaction. Task 3 uses browser acceptance on both architecture pages.
5. **Unexpected external requests or publication:** initial page/diagram load makes no external request, and first public deployment follows local acceptance. Tasks 3 and 5 inspect browser requests and verify the deployed artifact bytes.

---

### Task 1: Pin Archify project skill

**Files:**
- Create: `.agents/skills/archify/` from the official v3.0.1 release asset.
- Create: `.claude/skills/archify/` as an exact project-skill mirror.
- Create: `.agents/skills/ARCHIFY-MIT-LICENSE`.
- Modify: `skills-lock.json`.
- Modify: `.agents/skills/THIRD-PARTY-SOURCES.md`.

**Interfaces:**
- Consumes: upstream release tag object `679f195584e4216fd582c073d8964b3a9f59107e`, resolved commit and archive digest in Global Constraints.
- Produces: local CLI `node .agents/skills/archify/bin/archify.mjs`; `skills-lock.json` entry source `tt-a1i/archify`, immutable commit ref, `sourceType: github`, skill path `archify/SKILL.md`, verified computed hash.

- [ ] Fetch the official release archive; verify SHA-256 equals `b0b23bd28db314f04ca8ab9620fe20f8c1ac6474a3546bd8fe4679508aa1b7f5` before extraction. Extract only upstream `archify/`; do not vendor repository docs, gallery, release bundle, or `node_modules`.
- [ ] Preserve upstream MIT notice and source attribution; record the immutable commit and release digest; generate the skills lock hash using the existing project convention.
- [ ] Mirror the complete imported skill byte-for-byte into `.claude/skills/archify/`; do not independently edit either upstream copy.
- [ ] Verify `npx skills list --agent codex claude-code --json` discovers the Archify skill in both project-local agent trees and verify the checked-out source revision.
- [ ] Commit the imported skill, notice, license, and lock changes. Do not publish Pages or add a Pages workflow in this task.

**Verification:**

```bash
sha256sum archify.zip
npx skills list --agent codex claude-code --json
```

Expected: exact approved release digest and Archify recognized for Codex and Claude Code; lock points to immutable commit.

---

### Task 2: Generate and verify source-backed Archify diagrams

**Files:**
- Create: four `.archify/architecture-*` and `.archify/workflow-*` candidate folders, each with `candidate.json` and generated HTML.
- Create: `.archify/SHA256SUMS` and `.archify/site-manifest.json`.
- Create: `site/diagrams/vi/runtime-architecture.html`, `site/diagrams/vi/input-modes.html`, `site/diagrams/en/runtime-architecture.html`, `site/diagrams/en/input-modes.html`, and `site/diagrams/SHA256SUMS`.
- Create: `tools/regenerate_archify_diagrams.py`.
- Create: `tools/check_archify_artifacts.py`.
- Create: `test/test_archify_artifacts.py`.

**Interfaces:**
- Consumes: Task 1's pinned CLI and project source commit `87e6de6e59b96310876450a723e3b9ce5d613d41`.
- Produces: four standalone, source-linked Archify HTML paths listed above; a manifest mapping each candidate, generated output, and deployed copy; CLI checker `python3 tools/check_archify_artifacts.py --root .` with zero exit on exact manifest/hash/copy agreement and nonzero exit on mismatch.
- Task 3 uses the exact four `site/diagrams/<locale>/<name>.html` paths above. Task 4 uses the manifest checker and SHA files; path ownership remains with this task.
- `.archify/site-manifest.json` has `version: 1`, `archify_commit`, `source_revision`, and exactly four `artifacts` rows. Each row has `type`, `locale`, `candidate`, `generated`, `published`, `candidate_sha256`, `generated_sha256`, and `published_sha256`. `.archify/SHA256SUMS` covers candidates and generated HTML; `site/diagrams/SHA256SUMS` covers published HTML. Regeneration updates row hashes and both checksum files after reviewing the changed candidates.

- [ ] **Step 1: Write failing manifest-checker tests.** Use Python `unittest` fixtures with four valid entries. Assert valid candidates/outputs/site copies pass, a modified published HTML fails, a missing candidate fails, and a traversal path outside repository root fails.
- [ ] **Step 2: Run the focused tests and verify the intended failure.**

Run: `python3 -m unittest discover -s test -p 'test_archify_artifacts.py' -v`
Expected: FAIL because `tools.check_archify_artifacts` does not exist.

- [ ] **Step 3: Implement `check_manifest(root: Path) -> None` in `tools/check_archify_artifacts.py`.** Parse the manifest, require exactly one artifact per approved locale/type pair, reject paths outside root, verify manifest SHA-256 values against both sums files, and compare each generated `.archify` HTML byte-for-byte with its published `site/diagrams/` copy. Keep the implementation on Python standard library only.
- [ ] **Step 4: Re-run the focused tests.**

Run: `python3 -m unittest discover -s test -p 'test_archify_artifacts.py' -v`
Expected: PASS for valid provenance and rejection of changed/missing/traversal artifacts.

- [ ] **Step 5: Author two semantic candidates and their two locales.** Create an Architecture runtime map and a Workflow mode/fallback map; save each request's local timestamp once and use a separate `.archify/<type>-<slug>-<timestamp>/candidate.json` folder per locale/type. Include complete source evidence, pinned origin/revision, and `meta.quality_profile: "showcase"`. Use `meta.locale: "en"` for English and complete, manually reviewed canonical `meta.translations` with exact placeholders for Vietnamese `meta.locale: "vi"`.
- [ ] **Step 6: Review the four candidates before rendering.** Confirm each row's type/locale, candidate path, generated output path, published path, source revision, and source citations. Verify each candidate's `meta.output` matches its manifest `generated` path; do not edit generated HTML by hand.
- [ ] **Step 7: Run `ARCHIFY_UPDATE_CHECK_DISABLED=1 python3 tools/regenerate_archify_diagrams.py --root .`.** The script invokes Archify `finalize` using every row's `type`, `candidate`, and `generated` paths; requires all four validation/provenance/browser receipts to pass before copying generated files byte-for-byte to their `published` paths and updating both checksum files and hash fields. Check that each initially loaded artifact makes no external request.
- [ ] **Step 8: Commit candidate JSON, generated and published HTML, manifests, generator/checker, and passing tests.** Keep C++/Go product files unchanged.

**Primary evidence locations:** `src/lotus-engine.cpp:479-516`; `src/lotus-state.cpp:350-377,735-933,1206-1248`; `bamboo/bamboo-c.go:49-85,140-156`; `bamboo/bamboo-core/bamboo.go:60-94`; `settings-gui/core/dbus_handler.py:55-57,181-197`; `server/lotus-server.cpp:172-182,266-270,313-335,564-641`; `packaging/debian/control:28-43`. Re-read these at the pinned revision before citing line ranges.

**Verification:**

```bash
python3 -m unittest discover -s test -p 'test_archify_artifacts.py' -v
ARCHIFY_UPDATE_CHECK_DISABLED=1 python3 tools/regenerate_archify_diagrams.py --root .
python3 tools/check_archify_artifacts.py --root .
```

Expected: all four receipts show successful validation, strict provenance check, and browser check; all outputs pass manifest verification.

---

### Task 3: Build bilingual static pages

**Files:**
- Create: `site/index.html`, `site/en/index.html`, `site/architecture/index.html`, `site/en/architecture/index.html`.
- Create: `site/assets/site.css`.
- Modify: `README.md`, `README.en.md`.

**Interfaces:**
- Consumes: Task 2's four fixed diagram URLs, source snapshot SHA, and accurate product/installation/security claims.
- Produces: four no-JavaScript host pages and CSS; landing pages link to corresponding architecture routes. Architecture frames use relative diagram URLs, `title`, lazy loading and visible direct-open links; semantic text summaries remain outside frames. All language switches target the reciprocal route.

- [ ] **Step 1: Prove route acceptance fails before implementation.** Serve a temporary root containing no site at `/evkey-linux-community/`; use the real browser to visit the four planned routes. Expected: missing route / 404. Keep this smoke procedure temporary; do not add a source-text snapshot test.
- [ ] **Step 2: Implement Vietnamese and English landing pages, architecture pages, and responsive CSS.** Use the approved field-guide design. Give each page correct `lang`, canonical URL, reciprocal `hreflang`, relative intra-site/assets/frame links, non-affiliation copy, and build/source links. Do not imply binary releases exist. Use the approved English/Vietnamese Archify artifacts; include text alternatives, iframe titles, visible focus styles, and direct-open links.
- [ ] **Step 3: Add canonical Pages links to the Vietnamese and English root READMEs.** Keep other instructions unchanged.
- [ ] **Step 4: Re-run the same route test under the exact repo-prefix path using a local HTTP server and the real browser.** Visit all four host routes and four diagram frames; exercise both language switches, keyboard navigation and focus, direct-open links, 320px/narrow view, 200% zoom text alternatives, page overflow, canonical/hreflang destinations, and initially loaded browser network requests. Expected: all routes resolve under `/evkey-linux-community/`; no unexpected external request or broken link.
- [ ] **Step 5: Commit the four pages, CSS, and README links after browser acceptance.**

**Verification:** Real Chromium browser on the local site under `/evkey-linux-community/`; desktop plus narrow viewport, keyboard, visible focus, locale routes, embedded and direct diagrams, text alternative, and network inspection. No screenshot/visual-quality claim without inspecting the actual surface.

---

### Task 4: Add static Pages publishing and maintainer instructions

**Files:**
- Create: `.github/workflows/pages.yml`.
- Modify: `.github/workflows/check.yml` to run artifact unit tests on existing PR/push checks.
- Modify: `docs/development.md`.

**Interfaces:**
- Consumes: `site/` output and Task 2's `python3 tools/check_archify_artifacts.py`.
- Produces: a `main`-only static Pages artifact workflow; clear maintainer procedure for pin verification, local Archify regeneration, evidence updates, checksums, Chrome/Node prerequisites, and review of changed diagram semantics.

- [ ] **Step 1: Create workflow with empty default permissions.** The package job runs on `ubuntu-24.04`, uses checkout with `contents: read`, runs `python3 tools/check_archify_artifacts.py --root .`, then uploads only `site/` with `actions/upload-pages-artifact`. It does not run `npm` or download Chrome.
- [ ] **Step 2: Add separate deploy job.** Depend on package job; deploy only `refs/heads/main` using `actions/deploy-pages`; give it only `pages: write` and `id-token: write`; use the `github-pages` environment; do not check out repository source in deploy job. Serialize deploys without cancelling one in progress.
- [ ] **Step 3: Scope triggers.** Push to `main` only for `.archify/**`, `site/**`, or `.github/workflows/pages.yml`; allow manual dispatch but deploy only from `main`. Do not add pull-request deployments.
- [ ] **Step 4: Document exact Archify v3.0.1 commit and archive digest, checker and regeneration commands, candidate/output paths and hash manifests, Chrome/Node requirements, source snapshot links, and human regeneration/review steps in `docs/development.md`.** Keep existing native development and hardware-evidence guidance intact.
- [ ] **Step 5: Add `python3 -m unittest discover -s test -p 'test_archify_artifacts.py' -v` to existing `.github/workflows/check.yml` checks after the development harness; preserve existing triggers, permissions, and unrelated commands.**
- [ ] **Step 6: Check workflow/manifest locally and commit the workflow, normal check, and maintainer instructions.** No Pages repository setting change yet.

---

### Task 5: Locally verify, enable Pages, and publish

**Files:** No further planned source files. External repository setting: GitHub Pages build type.

**Interfaces:**
- Consumes: Tasks 1–4 complete, clean local review, all generated checksums, all four localized artifacts, and the locally accepted static site.
- Produces: successful workflow deployment and verified public site URL `https://dt418.github.io/evkey-linux-community/`.

- [ ] **Step 1: Run integration checks once, after all parallel work is integrated.** Run `python3 -m unittest discover -s test -p 'test_archify_artifacts.py' -v` and `python3 tools/check_archify_artifacts.py --root .`; rely on Task 2's four successful `finalize` receipts unless a candidate changed afterward. Inspect `site/` contents to ensure no root docs, dependencies, credentials, or unapproved files are included.
- [ ] **Step 2: Run local host acceptance.** Serve site at `/evkey-linux-community/`, open all four localized pages and each diagram in a real browser. Repeat keyboard, focus, narrow/zoomed text alternative, relative link, iframe/direct-open, and network checks. Do not enable Pages until all checks pass.
- [ ] **Step 3: Re-read Pages API state.** If site is still absent, create it with `gh api --method POST repos/dt418/evkey-linux-community/pages -f build_type=workflow` using authorized repository settings access. If site already exists, inspect and preserve its current workflow build type rather than POSTing again. If authenticated account lacks permission, stop and request only the needed settings action.
- [ ] **Step 4: Push the reviewed implementation commits to `main`.** Do not push before local browser acceptance and Pages workflow setup. Wait for the ordinary Check workflow and Pages deploy workflow; resolve real failures instead of hiding them.
- [ ] **Step 5: Visit the live site in Chromium.** Test all four public host routes and language switches; open each embedded diagram and its direct-open URL; confirm canonical project prefix, correct source snapshot, no broken requests, and that served HTML hashes match the committed `site/diagrams/SHA256SUMS`.
- [ ] **Step 6: Report actual deployed URL, Pages workflow run, and browser acceptance; note that Archify mobile diagram interaction is not promised.**

## Execution order and delegation

1. Complete Task 1 first; its source tree is required by Task 2.
2. After Task 1 is reviewed, Tasks 2 and 3 may run in one subagent wave. Their file ownership is disjoint: Task 2 owns `.archify/`, `site/diagrams/`, `tools/regenerate_archify_diagrams.py`, `tools/check_archify_artifacts.py`, and `test/test_archify_artifacts.py`; Task 3 owns four host pages, CSS, and root README links. Both consume the exact paths in this plan. Neither runs build/test/lint/formatters during the wave.
3. Fresh reviewer checks each task result against its own contract. Main session integrates and resolves shared-site-path/copy questions; Task 4 starts only after task outputs are settled.
4. Run acceptance once at integration checkpoints, then perform Task 5. First public deployment is the final external gate.

## Commits

Keep implementation commits scoped: imported Archify skill; diagrams/checker/tests; bilingual host pages/README; Pages workflow/maintainer docs. Push only after local acceptance and Pages workflow publishing are ready.