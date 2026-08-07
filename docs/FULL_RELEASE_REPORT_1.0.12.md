# CRC-LNM MCP 1.0.12 final report

## A. 原五模型审计

�?bundle �?seed 2024/3407/5280/7319/9021 五成员；只有合成 demo_case_001 可作部署接近性回归，没有可声称独立测试的�?seed 数据�?
## B. 选中的单模型

`seed_2024`，权�?SHA-256 `40e9fbed0da4fa915626e5c0bc6874a10a9129448271614fd011d31c46deeb17`�?
## C. 单模型选择依据

在唯一演示病例上最小化单成员概率与�?ensemble 概率�?MAE；不声称临床最优�?
## D. 单模型与 ensemble 差异

0.5726384521 �?0.6279473677，绝对差 0.0553089157；沿用阈�?0.3529504342，分类均�?1�?
## E. 六工具模块结�?
`contracts/`、`tools/`、`services/`、`inference/` 分层；一�?`server.py`、一�?STDIO 进程、精确六工具�?
## F. 六工具依赖边�?
信息/QC/特征/报告不导�?Torch；只�?prediction 进入 inference、预处理器和权重路径�?
## G. initialize/tools-list 是否导入 Torch

否；自动测试�?STDIO 冒烟验证，模型读取字节为 0�?
## H. 各工具是否加载模�?
�?`crc_lnm_predict_multimodal` 第一次调用加载，其他五项不加载�?
## I. 模型首次加载机制

首次预测校验 manifest、模�?预处�?checksum，延迟导�?Torch，构造一�?CPU eval/inference-mode 实例�?
## J. 模型复用和并发锁

双检锁保证并发首次调用只加载一次；失败状态缓存，避免并发加载风暴；第二次预测复用�?
## K. 病例资源策略

wheel 仅一份合�?JSONL；首次病例调用建�?byte-offset 索引；case_ref allowlist，无任意路径读取或安装目录写入�?
## L. 删除的运行依�?
pandas、sklearn、imbalanced-learn、训�?GPU依赖与项目直�?HTTP 依赖未进�?1.0.12�?
## M. 保留的运行依赖及理由

FastMCP、Pydantic、NumPy、PyTorch，理由见依赖审计�?
## N. 六工具契约变�?
移除 1.0.11 两个占位工具，恢复六�?`contract_version=1.1.0` 的正�?envelope；详�?contract diff�?
## O. 六个独立 smoke 结果

六项全部 PASS；各 JSON 位于 `reports/smoke_tool_*.json`�?
## P. 完整六工具流水线结果

PASS；见 `reports/six_tool_smoke_results.json`�?
## Q. 首次预测和第二次预测耗时

最�?wheel 2.068s �?0.019s�?
## R. 启动和模型加载内�?
轻量�?108 MB；完整链路峰�?282,402,816 bytes�?
## S. wheel 内容和大�?
2,921,012 bytes；仅 `crc_lnm_mcp` �?dist-info，含契约、服务、推理代码和受控 assets�?
## T. wheel 内模型文件数�?
严格等于 1：`crc_lnm_mcp/assets/model/model_state.pt`�?
## U. Python 版本测试结果

最终构建和完整运行验证�?Python 3.12；元数据支持 `>=3.10`�?.10/3.11 本轮未建立独�?wheel-only 环境�?
## V. 未验证风�?
无独立临床测试、单模型阈值未重校准、未�?ModelScope 公网冷缓存与 Linux 托管环境实跑�?.10/3.11 未单独运行�?
## W. 用户下一步发布操�?
审阅 wheel、checksum、依赖和风险后，由用户手工发�?PyPI，再�?README 唯一配置创建 ModelScope 托管实例。本次未发布或推送�?
## X. 回滚方案

停用 1.0.12 实例；从完整备份在新目录恢复，或重新建立只含占位工具�?1.0.11 金丝雀；不得覆盖不可变发布文件�?