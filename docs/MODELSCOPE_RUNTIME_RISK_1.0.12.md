# ModelScope runtime risk assessment 1.0.12

Risk level: **medium-low for release candidate; final ModelScope host validation remains required**.

Verified locally:

- Pure NumPy numerical equivalence passed on 101 inputs with probability max absolute error `6.556510925292969e-07` and zero class mismatches.
- Windows and WSL2 Ubuntu wheel-only matrices passed on CPython 3.10.20, 3.11.15, and 3.12.13.
- Linux and Windows empty-cache and warm-cache `uvx --from <wheel>` runs passed.
- Linux cold initialize completed in 102.18657 seconds; warm initialize completed in 2.767183 seconds.
- Linux complete installed environment was 124,068,695 bytes; uvx cache was 135,810,591 bytes; peak RSS was 115,572,736 bytes across the recorded cold/warm pair.
- Exactly six tools were exposed; the complete six-tool published-style pipeline passed on both operating systems.
- Model weights stayed lazy until the first prediction and were loaded once (`load_count=1`, `load_attempt_count=1`).

Residual risks:

- Tests used WSL2 Ubuntu, not the actual ModelScope container image, mirror, DNS, filesystem, quotas, or supervisor.
- Cold download time is network-sensitive: two successful Linux observations varied substantially (28.78 and 102.19 seconds to initialize).
- ModelScope health-check and process-lifecycle behavior must still be verified on the real host before broad rollout.

Recommendation: the local release gate permits a controlled ModelScope canary. Do not claim ModelScope production validation until the actual-host STDIO six-tool test passes.
