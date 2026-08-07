# Performance report 1.0.12

环境：Windows、Python 3.12、CPU、最�?wheel、正�?console script、官�?MCP STDIO client。完整六工具实测：initialize 2.118s，tools/list 0.003s，模型信�?0.004s，QC 0.007s，CT 0.009s，病�?0.007s，首次预�?2.068s，报�?0.011s，总计 4.927s。独立预测冒烟的第二次预测为 0.019s，证明实例复用�?
启动/轻量阶段峰值约 108 MB；加载模型后的完整链路峰�?282,402,816 bytes。最�?wheel �?2,921,012 bytes，SHA-256 �?`625d494a3b683c567b256d1de846ea126cf16b4b0b8cb0a5ff950c60416573e9`。无外网连接、无残留子进程、任�?CWD 零文件写入�?
这些是本机部署链路测量，不是 ModelScope 公网冷缓存时间，也不是模型临床性能声明�?