# Zelretch - Fonts

This folder is reserved for TTF / OTF font files used by image-generating
plugins (logo, glitch, profile card, ...).

The original Ultroid shipped with ~20 font files (~3.4 MB). Zelretch does
**not** bundle them by default for two reasons:

1. **Hugging Face Spaces** rejects binary files larger than ~10 MB in
   regular git pushes - they must be stored via
   [HF Xet](https://huggingface.co/docs/hub/xet). Bundling them in the
   default repo would break the one-command HF Spaces deployment.
2. **Most deployments don't need them.** The core Zelretch bot and the
   bundled addon plugins do not read any font files. Fonts are only used
   by image-manipulation plugins that have not yet been ported from
   Ultroid.

## Restoring the fonts (optional)

If you port an image plugin that needs a font, drop the corresponding
`.ttf` / `.otf` file into this folder. The plugin should reference it via:

```python
import os
FONT_PATH = os.path.join("resources", "fonts", "MyFont.ttf")
```

For Hugging Face Spaces deployments that need fonts, use
[Git LFS](https://git-lfs.com) or HF Xet to track the binary blobs:

```bash
git lfs install
git lfs track "resources/fonts/*.ttf" "resources/fonts/*.otf"
git add .gitattributes resources/fonts/
git commit -m "Add fonts via Git LFS"
git push
```
