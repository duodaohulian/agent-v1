# Torch to NumPy Equivalence 1.0.12

Status: **PASS** across 101 deterministic synthetic cases.

- Maximum layer error: `1.907348633e-06`
- Maximum logit error: `1.519918442e-06`
- Maximum probability error: `6.556510925e-07`
- Predicted-class mismatches: `0`
- Demo Torch probability: `0.5726384520530701`
- Demo NumPy probability: `0.5726382732391357`

All inputs are synthetic and finite. Both runtimes consume the exact same saved
preprocessing output. The conversion changes only the runtime implementation;
it does not retrain, recalibrate, or claim improved clinical performance.
