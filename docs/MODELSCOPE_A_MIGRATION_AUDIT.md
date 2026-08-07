# ModelScope 方案 A 迁移审计

审计日期�?026-08-04。审计对象是改造前备份
`release_1.0.10_backup_before_modelscope_canary_20260804`、当前工作区、PyPI 现有发布包，
以及参考仓�?`rpint/nfyy-ckd-risk-warning-mcp` �?`master` 分支�?
## 改造前启动�?
`uvx` 安装 `crc-lnm-medical-agent` �?两个 console script 之一进入
`wei_multimodal.mcp_server.__main__:main` �?导入 argparse、Uvicorn、HTTP 应用代码 �?读取 YAML �?package runtime assets �?`create_mcp()` 注册 lifespan �?lifespan 调用
`_build_runtime()` �?展开 JSONL 病例�?�?创建病例和产物仓�?�?`PredictionService` 校验�?加载五个 PyTorch 模型 �?MCP 才能稳定完成 initialize/tools/list�?
这条链同时承�?STDIO、Streamable HTTP、bearer middleware、health endpoint、host/origin
allowlist 等职责。ModelScope 方案 A 在看到工具列表前就可能因安装体积、Python 版本、缺�?重依赖、病例展开、模型加载、内存或超时失败�?
## 参考项目启动链

参考项�?`master` �?`pyproject.toml` 要求 Python >=3.10，只直接依赖 FastMCP �?Pydantic，并定义一个指�?`server:run` �?console script。`server.py` 创建 FastMCP�?`run()` 直接运行 stdio；`__main__.py` 只调用同一�?`run()`。README 的托管配置使�?`uvx` 和单一包名参数。仓库根目录没有独立 `modelscope-mcp.json`，配置位�?README�?
参�?smoke script 会发�?initialize、initialized �?tools/list，但不调用工具，也没有使�?当前官方 MCP 客户�?API。本项目复用其轻量启动外壳，不复�?CKD 业务、模拟数据、医学规�?或其不完整测试方式�?
参考来源：

- https://github.com/rpint/nfyy-ckd-risk-warning-mcp
- https://raw.githubusercontent.com/rpint/nfyy-ckd-risk-warning-mcp/master/pyproject.toml
- https://raw.githubusercontent.com/rpint/nfyy-ckd-risk-warning-mcp/master/src/nfyy_ckd_risk_warning/server.py
- https://raw.githubusercontent.com/rpint/nfyy-ckd-risk-warning-mcp/master/scripts/_smoke_stdio.py
- https://modelscope.cn/docs/mcp/create
- https://github.com/modelscope/modelscope-mcp-server

## 依赖差异

改造前项目直接依赖 MCP CLI、NumPy、Pandas、PyYAML、scikit-learn、imbalanced-learn�?Jinja2、Torch、Starlette �?Uvicorn，Python 范围�?>=3.12,<3.14。金丝雀项目只直接依�?`fastmcp>=2,<3` �?`pydantic>=2,<3`，Python 范围�?>=3.10。FastMCP 自身可能传递安�?HTTP 相关库，但金丝雀代码不直接导入、配置或启动 HTTP 服务�?
## wheel 内容差异

改造前本地工作区没�?`dist` 文件。通过已验证备份的临时副本实际构建�?1.0.5 wheel�?得到 17,530,379 字节�?1 个文件：66 �?`wei_multimodal` 条目�? �?`.pt`�? �?JSONL
�?16 �?deployment bundle 条目。改造后 wheel �?4,244 字节�? 个文件，仅有 4 �?`crc_lnm_mcp` 源文件和 5 �?dist-info 条目；体积下降约 99.98%。模型、权重、JSONL�?demo、Docker、configs、旧包和缓存均未进入 wheel�?
## 配置审计

改造前有根目录�?`configs/` 两份 ModelScope JSON，根结构、env 类型、server 名称和字�?均不一致；两份都固定旧版本并额外传 `--transport stdio` �?Torch 环境变量。改造后仅保�?根目�?`modelscope-mcp.json`，README 第一�?JSON 与其结构相等，只�?`uvx` 和单一包名
参数�?
## 本轮改变

- 新增独立、延迟构�?FastMCP �?`crc_lnm_mcp` 包�?- 仅暴�?`healthcheck` �?`describe_deployment`�?- �?pyproject 变为唯一版本源和精确 wheel 包发现规则�?- 删除重复正式配置和第�?console script�?- 增加 wheel 检查、发布检查、官�?MCP 客户�?smoke、任�?CWD �?stdout 安全测试�?- 将旧 HTTP/Docker/Nexent 说明隔离�?legacy 文档�?
## 本轮明确不改�?
- 不迁移六个医学工具�?- 不加�?Torch、五模型、病�?JSONL 或病例缓存�?- 不删�?`src/wei_multimodal` 医学源码�?- 不上�?PyPI、不 push GitHub、不登录或操�?ModelScope�?- 不声�?ModelScope 网站验证已经通过�?
## 启动资源对比

在本机对“仅导入入口模块”进行无模型/无病例读取对比：旧入口（Python 3.13）耗时
8.705 秒、RSS 363,843,584 字节；新入口（Python 3.10）耗时 0.071 秒、RSS
20,656,128 字节，入口导�?RSS 约下�?94.3%。不�?Python 运行时会影响绝对值，但旧入口
在导入时引入 Torch/HTTP/业务层而新入口不引入的根因不变�?