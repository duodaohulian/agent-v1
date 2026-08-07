# Lightweight runtime release gate 1.0.12

Status: **PASS for local release-candidate gates**.

## Runtime and numerical gate

- Backend: pure NumPy; source framework: PyTorch; selected model: `seed_2024`.
- Runtime asset SHA-256: `e837f8c299cf406827bc1cf0f892c0d053613ec0904ed0679ed5ba582e88832a`.
- Source weight SHA-256: `40e9fbed0da4fa915626e5c0bc6874a10a9129448271614fd011d31c46deeb17`.
- 101-case equivalence: layer max error `1.9073486328125e-06`; logit max error `1.519918441772461e-06`; probability max error `6.556510925292969e-07`; class mismatches `0`.
- Demo: PyTorch `0.5726384520530701`; NumPy `0.5726382732391357`; absolute error `1.7881393432617188e-07`; predicted class `1`.
- Threshold remains `0.3529504342004657`; it was not recalibrated.

## Platform matrix

All wheel-only environments passed dependency checks, six independent tool smokes, the complete six-tool chain, two predictions, probability regression, lazy single loading, clean stdout, child-process cleanup, runtime network checks, and arbitrary-CWD execution.

| OS | Python | Result | Peak RSS (bytes) |
|---|---:|---|---:|
| Windows 11 | 3.10.20 | PASS | 110,923,776 |
| Windows 11 | 3.11.15 | PASS | 117,256,192 |
| Windows 11 | 3.12.13 | PASS | 114,438,144 |
| WSL2 Ubuntu | 3.10.20 | PASS | recorded in individual smoke reports |
| WSL2 Ubuntu | 3.11.15 | PASS | recorded in individual smoke reports |
| WSL2 Ubuntu | 3.12.13 | PASS | recorded in individual smoke reports |

## uvx gate

| OS/cache | Initialize (s) | tools/list (s) | first prediction (s) | second prediction (s) | Peak RSS (bytes) |
|---|---:|---:|---:|---:|---:|
| Linux cold | 102.186570 | 0.004801 | 0.054591 | 0.007830 | 114,446,336 |
| Linux warm | 2.767183 | 0.008183 | 0.060333 | 0.007877 | 115,572,736 |
| Windows cold | 48.180069 | 0.003322 | 0.070239 | 0.010862 | 114,880,512 |
| Windows warm | 4.939355 | 0.006723 | 0.073154 | 0.010635 | 116,109,312 |

Linux dependency resolution, download preparation, and offline install were `0.273765`, `9.748105`, and `0.507160` seconds. The Linux installed environment was 124,068,695 bytes and the isolated uvx cache was 135,810,591 bytes. Complete uvx six-tool published-style smokes passed on Linux and Windows.

## Artifact gate

The candidate wheel is 2,932,183 bytes and contains exactly one runtime model (`model_runtime.npz`). It contains no `.pt`, `.pth`, `.ckpt`, Torch module, ONNX runtime, CUDA/NVIDIA package, or training resource. `twine check` and `scripts/check_release.py` passed.

No PyPI upload, GitHub push, or ModelScope operation was performed. Actual ModelScope-host validation remains pending.
