# ModelScope 手工部署说明（STDIO 金丝雀�?
## 发布对象

- PyPI 包名：`crc-lnm-medical-agent`
- 固定版本：`1.0.11`
- Python：`>=3.10`
- 直接依赖：`fastmcp==2.14.7`、`pydantic==2.13.4`
- 传输：仅 STDIO
- 工具：仅 `healthcheck` �?`describe_deployment`

本版本只验证托管平台从包安装�?MCP 初始化的完整链路，不加载模型、病例数据或六个医疗工具�?
## ModelScope 正式配置

仓库根目�?`modelscope-mcp.json` 是唯一正式配置。平台中填写�?
- command：`uvx`
- args：只填写一个�?`crc-lnm-medical-agent@1.0.11`
- 不填�?URL、host、port、transport、HTTP 参数或环境变�?
完整配置必须为：

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

## 发布前本地验�?
�?Windows PowerShell 中从仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release_verify.ps1
```

只有脚本最后输�?`LOCAL RELEASE VERIFICATION: PASS` 才表示本地门禁全部通过。该脚本不会上传 PyPI、推�?GitHub 或操�?ModelScope�?
## 平台验收

部署成功后确认：初始化完成；`tools/list` 仅返回两个工具；`healthcheck` 返回 `status=ok`、`version=1.0.11`；`describe_deployment` 返回 `medical_tools_enabled=false`；进程退出后无残留子进程�?
## 回滚

金丝雀异常时删除或停用该托管实例，不要切换�?HTTP 配置。旧医疗实现仍保留在源码树中，但不进�?1.0.11 wheel；后续迁移必须单独评审�?