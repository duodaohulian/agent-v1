# ModelScope Canary 1.0.11 发布记录

## 收口结论

1.0.11 是独立、轻量、仅 STDIO �?ModelScope 托管部署金丝雀。构建配置只发现 `src/crc_lnm_mcp`，wheel 内仅有四�?Python 文件和发行元数据。旧 `src/wei_multimodal`、模型、数据、HTTP/Docker/Nexent 资产均不进入 wheel�?
## 固定发布契约

- 包：`crc-lnm-medical-agent==1.0.11`
- Python：`>=3.10`
- 依赖：`fastmcp==2.14.7`、`pydantic==2.13.4`
- 控制台入口：`crc-lnm-medical-agent = crc_lnm_mcp.server:run`
- 工具：`healthcheck`、`describe_deployment`
- 版本来源：运行时通过 `importlib.metadata` 读取已安装发行版
- ModelScope 参数：`crc-lnm-medical-agent@1.0.11`

正式配置�?
```json
{
  "mcpServers": {
    "crc-lnm-medical-agent": {
      "command": "uvx",
      "args": [
        "crc-lnm-medical-agent@1.0.11"
      ]
    }
  }
}
```

## 验证口径

`scripts/release_verify.ps1` 负责清理旧产物、重新构�?wheel/sdist、执�?Twine 与静态发布门禁、运行默认金丝雀测试、在临时 wheel-only 环境完成真实 MCP STDIO 生命周期、检查任意工作目录启动、生成源码压缩包�?SHA-256。支持的 Python 3.10�?.11�?.12 还需分别从新 wheel 安装验证�?
`scripts/audit_uvx_cold_start.ps1` 使用隔离缓存拆分 Python 发现、虚拟环境、解析、安装、控制台初始化、冷启动和热启动耗时；详细安装输出写入独立日志，不污�?MCP STDIO�?
本机实测 uvx cold �?25.926�?0.876 秒，warm �?5.822�?.940 秒；主要差值来自空缓存依赖获取与工具环境物化，而非 Python 发现�?venv 创建。详�?`docs/UVX_COLD_START_AUDIT.md`�?
## 边界

本记录不授权上传 PyPI、推�?GitHub、创�?Release 或操�?ModelScope。金丝雀不提供医疗推断，不能用于临床决策�?