# Zelretch - Extras

This folder holds logos, thumbnails and tutorial markdown files used by
image plugins and the README.

The original Ultroid shipped with several JPG / PNG images in this folder.
Zelretch does **not** bundle them by default to keep the repo small and
compatible with Hugging Face Spaces (which rejects large binary files in
regular git pushes).

## Restoring the extras (optional)

Drop any required image assets into this folder. For Hugging Face Spaces
deployments that need binaries, use
[Git LFS](https://git-lfs.com) or [HF Xet](https://huggingface.co/docs/hub/xet).
