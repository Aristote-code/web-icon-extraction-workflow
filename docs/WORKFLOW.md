# Capture and verification procedure

## 1. Open the authorized session

Use Codex browser control to open the supplied application URL in the user's selected browser. Follow the browser tool's initialization instructions, name the session, and read the pageAssets capability documentation. Confirm the actual application loaded and record login, permissions or onboarding boundaries. Use the documented APIs rather than reading browser profiles or cookies from disk.

## 2. Establish a route inventory

Read same-workspace links from the current rendered page. Visit navigation sections, spaces, folders, lists and existing content detail pages. Resolve routes through observed links; do not guess private object IDs. Record final URLs after redirects. Keep aliases distinct from pages that actually failed. Do not interpret an empty page, partial shell or a navigation timeout as proof of full page coverage.

For the recorded ClickUp run, the inventory included Inbox tabs, Planner, AI, Teams, Docs, Dashboards, Whiteboards, Forms, Clips, Goals, Timesheets, assigned comments, skills, artifacts, meetings, My Tasks, All Tasks, Product Design, Team Space, Sprints and Projects, list/board/calendar/gantt/table/timeline/workload views, tasks, documents and App Center.

## 3. Capture meaningful states

Load `workflow/capture.js` into the initialized cua_repl environment. Bind `tab` using the documented API, then create a capture function with an absolute local output path:

```js
let capture = await createIconCapture(tab, captureRoot);
nodeRepl.write(await capture('Inbox — Primary — loaded'));
```

Capture after the application has visibly loaded, after opening relevant menus, and after scrolling a lazy-loaded asset picker. The helper reads SVG markup, sprite symbols, use references and page links, bundles currently observed images, and saves a self-contained input directory. It only captures the current page state; navigation and coverage judgment remain explicit.

A page can mount many shared symbols without displaying all of them. Preserve that distinction in provenance. Inspect `use` references and the downloaded sprite resource; when an original sprite is successfully captured, split all its symbols even if individual screen use is unknown. Do not infer that a failed request means an asset is unavailable if a later capture downloaded the same resource.

For picker coverage, record successive item counts and scroll positions until both the bottom position and total count stabilize. In the ClickUp run, 12 scroll positions exposed 608 entries, reduced to 603 unique normalized pictograms. No icon was selected.

Do not create content, install integrations, change configuration, send messages or delete data merely to expose more icons. Record these limits instead. Opening documents may affect normal last-viewed history.

## 4. Package and deduplicate

Run `scripts/package_assets.py --input RUN_DIRECTORY --output BUILD_DIRECTORY`. Input captures must match the helper's schema; paths to originals can be relative to the input directory. The packager also accepts the compressed case-study inputs.

The packager retains original image bytes, raw inline/symbol markup, and normalized standalone SVG exports. Referenced definitions found in captured SVGs are copied into exported symbols. Deduplication uses SHA-256 of normalized XML, not visual similarity. It strips framework attributes and presentation classes; CSS variable fallbacks are used when available. Fixed colors and currentColor remain. The viewBox defaults to 24×24 only when none was present; review such exports against the original markup.

For a new run, update run metadata in the packaging script and create a new coverage assessment. Its gallery/header defaults are from the ClickUp case study. Never copy the recorded finalizer's route coverage claims into a new report.

## 5. Verify the evidence boundary

Check XML parsing, hash integrity, definition closure, renderability and a visual sample. Flag transparent results, unsupported SVG/CSS features and incomplete definitions instead of silently treating them as usable icons. CairoSVG can differ from browser rendering. Retained raw markup and the original sprite are the source of truth for comparison.

Report separately:

- Original downloaded SVGs and sprite contents.
- Geometry captured from the rendered DOM or picker.
- Verified visible usage versus definitions merely present in a resource.
- Loading shells, empty states, disabled controls and navigation failures.
- Discovered but unvisited routes, including aliases.
- Unexplored creation flows, permission gates, themes and responsive variants.

Save a downloadable ZIP, manifest with provenance and hashes, an asset gallery, coverage report and validation log. Do not claim complete application coverage unless the route and state inventory actually establishes it.
