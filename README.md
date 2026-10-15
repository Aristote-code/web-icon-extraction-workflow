# Universal web icon extraction workflow

A reusable, browser-assisted flow for bulk extraction of icons and pictograms from **any authorized website or web app**. Configure a target, explore accessible routes and UI states, capture original images and vector geometry, then generate deduplicated SVGs, a searchable gallery, provenance manifests, a coverage report and a ZIP.

The shared pipeline has no fixed application domain, workspace ID, icon classes, route names, capture numbers or historical findings. [ClickUp](examples/clickup/README.md) is an optional example dataset.

## The flow

1. **Define the run.** Set the entry URL, scope, title, date and known limitations in `run.json`.
2. **Discover and inspect.** Use an authorized browser session to visit observed links, menus, tabs and lazy-loaded pickers without saving changes.
3. **Capture.** Use `workflow/capture.js` inside Codex browser control to collect each meaningful state and downloaded original images.
4. **Extract and normalize.** Reconstruct inline SVGs, local and downloaded external sprite references, all symbols in original sprites, and standalone original SVGs. Retain original bytes and raw markup.
5. **Deduplicate and verify.** Hash normalized SVGs, resolve available definitions, flag missing references and inferred dimensions, and optionally render previews.
6. **Deliver.** Export an asset gallery, JSON/CSV manifests, captured-state coverage, download failure records, discovered unvisited routes and a ZIP.

This is a universal workflow and capture/processing toolkit, with explicit browser navigation and coverage judgment. It is not an unattended crawler. Site-specific selectors are optional configuration, not assumptions built into the shared exporter.

## Start a run

Copy [`config/run.example.json`](config/run.example.json) to your capture directory as `run.json`, and change the target and scope. In an initialized Codex browser-control session, load `workflow/capture.js`, bind the current tab using the documented API, and create the helper:

```js
let capture = await createIconCapture(tab, captureRoot, {
  run: runConfig,
  pictogramSelector: '' // Optional observed selector matching SVGs inside a picker.
});
nodeRepl.write(await capture('Inbox — loaded', {
  status: 'rendered state verified',
  notes: 'Main content visibly loaded; shared symbols also captured.'
}));
```

`captureRoot` is an absolute output directory, and `runConfig` is your parsed run metadata. Capture after navigation and after exposing relevant UI states. Scroll lazy-loaded asset lists until their count and bottom position stabilize. The helper reads the current document, open shadow roots and accessible same-origin frames; inaccessible frames are counted in capture metadata.

## Build the outputs

Packaging requires Python 3.9+ and its standard library:

```sh
python3 scripts/run.py --input runs/my-site --output build/my-site-assets
```

This creates `build/my-site-assets/` and `build/my-site-assets.zip`. Open `coverage-report.html` or `gallery.html` inside the output directory.

Optional rendering checks require CairoSVG, Pillow and the native Cairo library:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run.py --input runs/my-site --output build/my-site-assets --render
```

If your installed native Cairo library is not found, set `CAIRO_LIBRARY_PATH` to its absolute library-file path.

Without `--render`, rendering is explicitly marked **not requested**, rather than assumed successful. Rendering skips recorded external dependencies; those remain flagged for review. Run the command again to rebuild from captures.

To try the complete packaging/report flow with existing evidence:

```sh
python3 scripts/run.py --input examples/clickup/data --output build/clickup-example
python3 -m unittest discover -s tests
```

## Outputs and evidence

| Output | Purpose |
|---|---|
| `originals/` | Exact downloaded image bytes, including original sprite files |
| `svg/` | Normalized standalone exports |
| `incomplete-svg/` | Exports with missing local definitions |
| `raw-symbols/`, `raw-inline/` | Original extracted markup |
| `manifest.json`, `manifest.csv` | Asset hashes, source URLs/states, symbol IDs, types and checks |
| `gallery.html` | Search and download extracted assets |
| `coverage-report.html`, `coverage.json` | Captured states and observed access/loading limitations |
| `validation.json` | Parsing, missing definitions, optional rendering and transparent results |
| `discovered-unvisited-links.json` | In-scope links without an exact-URL capture, including possible aliases |
| `download-failures.json` | Failed attempts, with flags for later successful downloads |

Categories overlap. A sprite definition's presence proves availability, not visible use. Coverage reports derive from the current run's captures and supplied observations; they do not infer that an entire application was exhausted or that no changes occurred.

## Practical limits

Original SVGs and sprite geometry take priority. CSS-dependent appearance, icon fonts, canvas/WebGL content, closed shadow roots, cross-origin frames and unobserved network assets can require additional site-specific inspection. Raster originals are retained but not converted into invented vectors. External resources are resolved only when already downloaded. Normalized XML hashes are deterministic but are not perceptual deduplication. Raw markup remains available where class removal or CSS dependencies affect appearance.

Keep authenticated captures private. They can contain workspace URLs and titles. Do not commit browser profiles, cookies or access tokens. Extraction does not grant a license to reuse third-party artwork.

See [the full workflow](docs/WORKFLOW.md) and [the capture schema](docs/CAPTURE-SCHEMA.md).
