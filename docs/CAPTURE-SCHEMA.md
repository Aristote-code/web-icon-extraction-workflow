# Capture input format

Each `captures/N.json` (or `N.json.gz`) contains:

```json
{
  "label": "Inbox Primary loaded",
  "dom": {
    "url": "https://example.com/workspace/inbox",
    "title": "Inbox",
    "svgs": ["<svg viewBox=\"0 0 24 24\">...</svg>"],
    "symbols": ["<symbol id=\"search\" viewBox=\"0 0 24 24\">...</symbol>"],
    "uses": ["#search"],
    "links": [{"text": "Home", "href": "https://example.com/workspace/home"}]
  },
  "bundle": {
    "assets": [{
      "kind": "image",
      "url": "https://example.com/media/icons.svg",
      "name": "icons.svg",
      "contentType": "image/svg+xml",
      "path": "originals/hash-icons.svg"
    }],
    "failures": [{"url": "https://example.com/media/missing.svg", "reason": "download failed"}]
  }
}
```

Capture IDs determine numeric ordering. `path` is resolved relative to the input directory unless absolute. Use portable relative paths for checked-in datasets. The case study stores only image downloads and geometry/route snapshots; the full page asset inventory and full accessibility transcripts were not committed.

Optional `state-N.txt` files contain loading indicators used for coverage flags. They need not contain document text. A loading flag is conservative evidence, not a reliable judgment about every part of a page.

## Run metadata and observations

The shared exporter reads `run.json` (or `--config FILE`) for `name`, `entryUrl`, `date`, `timezone`, `scope.origin`, `scope.pathPrefix`, `limitations` and `notes`. No application-specific values are required. See `config/run.example.json`.

Each capture can additionally supply:

```json
{
  "observation": {"status": "partial", "notes": "Main content still loading."},
  "dom": {
    "pictogramSvgs": ["<svg viewBox=\"0 0 48 48\">...</svg>"],
    "rootCount": 1,
    "inaccessibleFrames": 0
  }
}
```

`pictogramSvgs` explicitly identifies a subset of `dom.svgs`; absent this classification, SVGs use the generic inline category. It can be collected using an optional observed picker selector. Unknown status defaults to “DOM captured; page completeness not assessed.” Root/frame counts describe the capture boundary and are not claims about unseen content.
