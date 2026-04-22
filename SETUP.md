# 部署与运行

## 安装

```bash
git clone https://github.com/yuyuyuyu52/browser-use.git
cd browser-use
pip install -e .
```

如果服务器有系统代理，额外安装：

```bash
pip install python-socks
```

## 配置

编辑 `run_reply_task.py`，按需修改：

- `CDP_URL` — 远程 Chrome 的 CDP 地址
- `REPLY_COUNT` — 回复次数（默认 5）
- `INTERVAL_BASE` / `INTERVAL_JITTER` — 回复间隔秒数（默认 120±60）
- `api_key` — Google AI Studio API Key

## 运行

```bash
python run_reply_task.py
```

## 要求

- Python >= 3.11
- 远程 Chrome 需开启 CDP（`--remote-debugging-port=9223`）
- 网络能访问 CDP 地址和 Google API
