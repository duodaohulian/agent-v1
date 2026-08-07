# Inference Operator Audit 1.0.12

The verified seed_2024 model is a fixed float32 evaluation graph with 763,842
parameters across 66 state arrays. It contains Linear, exact GELU
(`approximate="none"`), LayerNorm (`eps=1e-5`), Embedding, concatenation,
stacking, a fixed four-head attention block, residual addition, and Softmax.

Evaluation-mode Dropout is a no-op. The model contains no BatchNorm,
convolution, sparse operation, dynamic control flow, custom operation, or CUDA
requirement. The attention dimensions are fixed: embedding 128, four heads,
head dimension 32, query length 1, and context length 5. The saved packed Q/K/V
and output projection weights are sufficient for a complete NumPy equivalent.

The full state inventory, shapes, dtypes, checksums, and parameter counts are in
`reports/inference_operator_graph.json`. This audit supports the pure NumPy
runtime decision; ONNX Runtime is not required.
