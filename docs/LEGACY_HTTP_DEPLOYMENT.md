# Legacy HTTP / Docker / Nexent Deployment

此文档仅保存旧部署路径的边界，不用于 ModelScope 方案 A�?
�?`wei_multimodal` 实现同时支持 Streamable HTTP、bearer middleware、请求体限制�?`/health/live`、`/health/ready`、host/origin allowlist �?Uvicorn。它需要模�?bundle、病�?数据、PyTorch 与可写的病例/产物目录。Docker/Nexent 路径也依赖这些完整医学资源�?
金丝雀 wheel 明确排除上述代码和资源。不要把 HTTP URL、host、port、bearer token�?Docker command、Nexent URL �?Torch 环境变量复制到根 ModelScope 配置。需要恢复旧部署时，
使用改造前备份或对应历�?Git 提交，在隔离环境中重新验证完整依赖和六工具；不要修改本次
金丝雀 wheel 来混合两种模式�?