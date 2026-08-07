# Full Runtime Baseline Audit

## Legacy implementation

The six tool adapters are under `src/wei_multimodal/mcp_server/tools`; their business services are under `src/wei_multimodal/mcp_server/services`. The 1.0.11 canary shell is under `src/crc_lnm_mcp`. The legacy lifespan eagerly expands case JSONL and creates the five-member prediction service.

## Models

All five members use `attention_path_ct_clinical` and the same schema and preprocessor.

- `seed_2024`: 3075485 bytes, load 0.137120s, inference 0.082179s, observed RSS 353869824 bytes.
- `seed_3407`: 3075485 bytes, load 0.037161s, inference 0.007537s, observed RSS 355164160 bytes.
- `seed_5280`: 3075485 bytes, load 0.036032s, inference 0.007758s, observed RSS 354889728 bytes.
- `seed_7319`: 3075485 bytes, load 0.034918s, inference 0.009316s, observed RSS 354959360 bytes.
- `seed_9021`: 3075485 bytes, load 0.035148s, inference 0.006384s, observed RSS 354959360 bytes.

## Locked inference contract

- Pathology dimensions: 768.
- CT dimensions: 1409 (14/93/744/558).
- Clinical order used by inference: age, male, Type, T.
- Feature-order SHA-256: `d4a5ecb56733db87f505473a7be1497a7fdd174c0994748d5b9574f7373d3200`.
- Threshold: 0.3529504342004657 from the evaluation-bundle OOF Youden record.
- Prior measured entry import: about 8.7s and 364 MB RSS; prior 1.0.11 wheel: 4,307 bytes. Current per-member measurements are listed above.
