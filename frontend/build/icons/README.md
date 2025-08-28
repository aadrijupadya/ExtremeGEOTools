# Icon drop folder

Place brand icons here and reference them by file name from the app.

File naming:
- openai.svg
- perplexity.svg

Guidelines:
- Artboard: 24x24 or 32x32 viewBox, transparent background.
- No outer padding; the glyph should comfortably fill the viewBox.
- Prefer single‑color (monochrome) or white on transparent.
- SVG preferred; PNG fallback works if square (>=64x64).

Usage:
- The app loads icons from `/icons/<name>.svg` (falls back to `.png`) via the `BrandIcon` component.
- Size is controlled by the `size` prop (default 18px).
