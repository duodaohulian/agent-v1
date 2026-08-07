# Dependency audit 1.0.12

The default runtime dependencies are exactly:

- `fastmcp==2.14.7`
- `pydantic==2.13.4`
- `numpy==2.1.3`

PyTorch is used only by the offline conversion/reference scripts and is not a default dependency or wheel member. The wheel metadata does not directly declare Torch, torchvision, torchaudio, ONNX, ONNX Runtime, pandas, scikit-learn, imbalanced-learn, CUDA, or NVIDIA packages. Transitive FastMCP dependencies remain managed by the pinned FastMCP release.

On WSL2 Ubuntu with CPython 3.12.13, the resolved runtime environment contained 81 packages, occupied 124,068,695 bytes (site-packages: 124,032,271 bytes), and passed `uv pip check`. The isolated download cache was 132,142,368 bytes. Explicit checks found none of Torch, torchvision, torchaudio, ONNX, or ONNX Runtime.

The blocked Torch baseline exceeded 1,804.03 seconds without reaching MCP initialize and grew its uv cache to about 897 MB. The lightweight Linux uvx run reached initialize in 102.19 seconds in the observed cold-cache run and used 135,810,591 cache bytes, reducing elapsed time by at least 94.3% and cache footprint by about 84.9% relative to that incomplete baseline.
