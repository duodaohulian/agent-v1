# UVX 冷启动分段审�?
## 目的

此前一�?ModelScope/本机隔离缓存探测观察到约 **100.377 �?*的首�?`uvx` 总耗时。单一总数无法判断瓶颈属于 Python 发现、环境创建、依赖解析、下�?安装，还�?MCP 控制台到 initialize，因�?1.0.11 增加可重复的分段审计�?
## 方法

`scripts/audit_uvx_cold_start.ps1` 只使用当�?`dist` 中的新本�?wheel，不读取可编辑源码，也不调用已发布的 PyPI 包。每�?Python 运行时使用独立的空缓存和临时目录，记录：

1. `uv --version` �?`uv cache dir`�?2. Python 发现以及是否发生 Python 下载（命令强�?`--no-python-downloads`）；
3. `uv venv`�?4. `uv pip compile` 解析�?5. `uv pip install` 下载/安装�?6. 已安装控制台�?MCP initialize�?7. �?`uvx` 缓存�?cold 总耗时�?8. 同缓存、同命令�?warm 总耗时�?
解析和安装的 verbose 输出写入每个运行时独立日志，MCP JSON-RPC 仍只�?STDIO，日志不会混入协�?stdout。命令示例：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/audit_uvx_cold_start.ps1 -Uv <TEMP_WORKSPACE>\path\to\uv.exe -KeepLogs
```

## 结果

2026-08-04 使用 `uv 0.12.1` 和本�?1.0.11 wheel 实测如下，三个运行时均强�?`--no-python-downloads`，没有下�?Python�?
| Python | 发现 | venv | 解析 | 安装 | 已安�?console 全流�?| uvx cold | uvx warm |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3.10.20 | 0.249 s | 0.206 s | 5.521 s | 13.247 s | 8.334 s | 40.876 s | 6.940 s |
| 3.11.15 | 0.170 s | 0.064 s | 5.956 s | 14.108 s | 8.099 s | 26.366 s | 6.685 s |
| 3.12.13 | 0.204 s | 0.052 s | 5.957 s | 14.315 s | 7.454 s | 25.926 s | 5.822 s |

Cold 中从启动 `uvx` �?MCP initialize 的时间分别为 38.303�?4.352�?3.975 秒；warm 对应 4.810�?.625�?.060 秒。原始结构化结果保存�?`docs/uvx-cold-start-results.json`�?
## 瓶颈判断

Python 发现�?venv 创建都小�?0.25 秒，不是此前�?100.377 秒的主要来源。显式分段中，依赖安装是最大单项（13.247�?4.315 秒），其次是解析�?.521�?.957 秒）；uvx cold �?warm 的差值为 19.581�?3.936 秒，说明空缓存工具环境的依赖获取/物化是主要冷启动成本�?.10 �?cold 明显更慢，但单机一次样本不足以归因�?Python 版本本身�?
本机包访问经 `127.0.0.1:7897` 本地代理发生；warm 采样只观察到 MCP/进程间的本机连接。严格的发布 smoke 在三�?Python 上均未观察到�?loopback 网络违规。上述结果既不能证明 ModelScope 一定超时，也不能证明一定不会超时�?
## 解释边界

Cold `uvx` 包括安装器可能产生的外部包索引连接；这不等于 MCP 服务使用网络传输。服务启动后的协议仍�?STDIO，两个金丝雀工具自身不访问网络。不同机器、缓存和镜像条件会显著改变总耗时�?