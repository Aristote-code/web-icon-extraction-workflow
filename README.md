# Bulk icon & pictogram extraction workflow

A browser-assisted workflow for collecting original SVGs, sprite symbols and inline pictograms from authenticated web applications, with deduplication, provenance and explicit coverage limits.

This repository contains the **actual ClickUp extraction performed on 15 October 2026**, its portable capture inputs, reusable capture/packaging code and a downloadable result. The capture helper runs inside Codex's browser-control session; this is not an unattended crawler or a standalone browser extension.

## Recorded results

| Measurement | Result |
|---|---:|
| Captured interface states | 74 |
| Distinct final URLs | 49 |
| Deduplicated SVG exports | 2,209 |
| Symbols in original downloaded sprite | 1,321 |
| Unique picker pictograms | 603 |
| DOM symbol exports | 329 |
| Original downloaded image files | 33 |

Source categories overlap. Counts include SVG geometry exports and auxiliary graphics, rather than 2,209 distinct visible interface icons. Validation found 10 exports with unresolved local definitions, one CairoSVG rendering error and 49 fully transparent 64px previews. See the packaged report for the precise boundary of verified assets.

**[Download the actual extraction ZIP](results/clickup-icons-and-pictograms.zip)**. Unzip it and open `clickup-assets/coverage-report.html` or `clickup-assets/gallery.html`. The ZIP contains individual SVGs, the original sprite, raw markup, manifests, coverage records, failure logs and evidence.

![Preview of extracted assets](results/clickup-preview.png)

## Reproduce the recorded extraction outputs

Python 3.9+ is required for packaging. Rendering additionally requires CairoSVG, Pillow and the native Cairo library (for example `brew install cairo` on macOS, or your Linux distribution's Cairo package).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/package_assets.py --input data/clickup --output build/clickup-assets
python scripts/finalize_clickup_case_study.py --input data/clickup --output build/clickup-assets
python scripts/verify_package.py build/clickup-assets
python -m unittest discover -s tests
```

The packaging command normalizes captures and exports symbols. The finalizer performs rendering checks, separates incomplete SVGs, generates the ClickUp coverage report and creates `build/clickup-icons-and-pictograms.zip`. Run packaging before finalization on every rebuild. The case-study finalizer includes observations from this recorded run; **do not use its narrative as evidence for a new run**. See [the workflow](docs/WORKFLOW.md) to collect and assess a new application.

The repository sorts reconstructed definitions deterministically. Rebuilt files can have different byte hashes from the archived original run when only definition order changed; the regression check verifies stable hashes across Python hash seeds.

## Repository contents

- `workflow/capture.js`: reusable current-state capture helper for Codex browser control.
- `scripts/package_assets.py`: local SVG reconstruction, normalization, deduplication and provenance.
- `scripts/finalize_clickup_case_study.py`: recorded-run reporting, rendering checks and ZIP generation.
- `scripts/verify_package.py`: file integrity and inventory validation.
- `data/clickup/`: compressed SVG/route captures and original image files, with portable relative paths. Full accessibility transcripts and browser sessions are excluded.
- `results/`: verified downloadable package and preview from the original run.
- `docs/WORKFLOW.md`: discovery, capture, coverage and review procedure.

## Scope and handling

The original run used an already authenticated session. It inspected navigation, menus, view types, tasks, documents, App Center and all lazily loaded entries in the icon picker without saving changes. It did not exhaust every accessible route, feature gate, menu, theme or creation flow. Mounted sprite definitions demonstrate availability, not visible use on a particular screen.

Capture files and manifests contain workspace URLs and some page/link titles. Keep authenticated runs private and review files before sharing. Browser profiles, cookies and access tokens do not belong in this repository. Extracted ClickUp and integration assets remain subject to their owners' rights; this repository grants no reuse license for them.
