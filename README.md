# CRC-LNM Medical Agent 1.0.16

面向 ModelScope 托管 STDIO 的完整懒加载�?NumPy 单模型版本。一�?console script、一个进程内注册六个医学工具；initialize �?tools/list 不读取模型参数或展开病例。第一�?`crc_lnm_predict_multimodal` 调用校验并加载唯一�?`seed_2024` NumPy runtime asset，后续预测复用同一实例。默认安装不依赖 PyTorch、NVIDIA �?CUDA 包�?
## 更新说明 (v1.0.16)

- **回滚 tool 签名�?GitHub v1.0.12 风格**：重新使�?`Literal["1.1.0"]` + `UUID4` + Pydantic BaseModel 嵌套输入（`input: PredictMultimodalInput`），恢复 FastMCP 2.14.7 �?ModelScope STDIO 上的兼容�?- **保留 v1.0.16 的中�?description 字段**�? 个工具的 `TOOL_DESCRIPTION` 完整保留，便�?Nexent/Claude Desktop JSON-RPC 客户端解�?- **PyPI 包名不变**：`crc-lnm-medical-agent-twomeme`，最新版�?1.0.16

## ModelScope 正式配置

```json
{
  "mcpServers": {
    "crc-lnm-medical-agent-twomeme": {
      "command": "uvx",
      "args": [
        "crc-lnm-medical-agent-twomeme@1.0.16"
      ]
    }
  }
}
```

ModelScope 中选择托管部署�?STDIO；command �?`uvx`，args 只填上面一个带版本参数。不要增�?URL、host、port、transport 参数或环境变量�?
## 本地验收

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release_verify_full.ps1
```

六工具为模型信息、病例质控、CT 特征准备、病理特征准备、单模型预测和报告生成。内置病例仅为合成演示资源；本包只用于科研辅助，不构成诊断，所有输出均需专家复核