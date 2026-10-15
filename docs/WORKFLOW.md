# Universal extraction procedure

## Configure the target

Create `run.json` from `config/run.example.json`. Set a descriptive name, entry URL, scope origin and path prefix. Optionally supply an ISO date and timezone; omitted dates use the current UTC date. Record limitations and notes based on this run, not a previous application. `--config FILE` overrides the input directory's metadata.

Scope controls the report's discovered-route inventory; the operator must also stay within that authorized boundary during browser navigation. Asset CDN URLs can differ from page origins and are retained when observed through the authorized page.

## Discover routes and states

Open the supplied URL through the selected browser's documented API. Confirm authentication and the actual application state. Read observed links and navigation labels. Visit accessible subpages and existing content; do not guess private object IDs. Record final URLs after redirects and distinguish routing aliases from failures.

Inspect menus, tabs, existing view types, empty states and accessible icon/pictogram catalogs. Loading shells need an explicit observation and a later loaded capture where possible. Do not create content, install integrations, submit forms or change settings simply to expose more assets. Log boundaries where access or configuration would be required.

There is no universal finite inventory of every interactive state. Capture counts demonstrate recorded coverage; they do not by themselves prove exhaustive coverage.

## Capture assets

Read the browser tool's initialization and pageAssets documentation. Load `workflow/capture.js` into the initialized cua_repl session. Use `createIconCapture(tab, captureRoot, options)`, with optional `options.run` metadata and an observed `options.pictogramSelector` matching SVGs inside an asset picker.

The returned `capture(label, observation)` reads the current document, open shadow roots and accessible same-origin frames. `observation.status` and `observation.notes` describe what was actually verified. Without observations, page completeness remains unknown. Cross-origin or inaccessible frames are counted in capture metadata; closed shadow roots are not inspectable by this helper.

The helper stores original image downloads and SVG/route snapshots with portable file paths. It does not save authentication storage or the full network inventory. Original sprite maps must be successfully downloaded before their external references can be reconstructed. CSS images depend on the pageAssets inventory; fonts and canvas drawings need separate analysis. A mounted definition proves availability, not visible use.

For lazy-loaded pickers, capture successive scroll states. Record entry counts and scroll positions until both stabilize at the bottom. Do not assume a particular class name, count or icon naming scheme. Optional selectors classify captured pictograms without changing the application's UI.

## Process and deliver

Run `python3 scripts/run.py --input RUN --output BUILD`. It packages SVGs, exports the report and gallery, verifies hashes and creates a ZIP next to BUILD. Add `--render` only after installing the optional rendering dependencies and native Cairo library.

The exporter splits all symbols in downloaded sprites, copies available definitions, resolves local use instances and external use instances backed by downloaded files, and normalizes standalone original SVGs. Downloaded source bytes and raw markup remain available. It strips framework/presentation attributes; fixed colors and currentColor remain. ViewBox inference and external dependencies are flagged in the manifest. Missing local definitions go to `incomplete-svg/`.

Deduplication uses normalized SVG hashes with deterministic definition order, rather than visual similarity. Visually equivalent but structurally different paths may remain. External resources are not fetched by rendering checks. XML parsing, source availability, renderability and browser fidelity are separate evidence categories.

Review the resulting gallery and validation log, especially missing paints or clipping, inferred dimensions, CSS-dependent SVGs, transparent results and renderer errors. Without optional rendering, the report explicitly records that rendering was not requested. Reports never claim that a visual sample was inspected automatically.

Report observed loading/authentication/permission limits, discovered unvisited links, unavailable assets and unexplored UI states. A failed download that later succeeded is distinguished from an unrecovered failure. Preserve category overlap and avoid presenting mounted definition counts as visible icon counts.

## Keep runs separate

Use a new input/output directory for each target or session. Authenticated data may contain private URLs or titles. Keep it private and exclude cookies, profiles and tokens. The optional `examples/clickup/` directory preserves one historical case; its route names and findings are not shared defaults. Third-party asset ownership and reuse rights remain with their owners.
