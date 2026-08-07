# Contract diff: 1.0.11 �?1.0.12

1.0.11 �?`healthcheck` �?`describe_deployment` 两个金丝雀占位工具被移除�?.0.12 在同一 STDIO server 中精确注册六个正式工具：模型信息、病例质控、CT 特征、病理特征、单模型预测、报告生成�?
公共 envelope 固定 `contract_version=1.1.0`，携�?request/trace ID、结构化 status/errors/warnings/provenance。输入以受控 `case_ref` 和短期内�?artifact ID 串联，禁止任意本地路径。预测结果新增并明确公开 `member_count=1`、`ensemble_enabled=false`、selected model/seed、阈值来源、人工复核与科研用途声明。报告只消费已有 artifact，不触发模型加载�?
这是有意的不向后兼容工具面变更；ModelScope 配置仍保持一�?`uvx` 参数，版本升级为 1.0.12�?