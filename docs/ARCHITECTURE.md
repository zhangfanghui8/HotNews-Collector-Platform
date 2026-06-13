# 系统架构

## 数据流

```
采集 (Adapter) → 规则层 (post_process) → 格式化 (format_report) → 分发 (Dispatcher，可选)
```

## 数据处理分工

| 层级 | 模块 | 职责 |
|------|------|------|
| L1 采集 | `scripts/adapters/` + `main.py` | 各维度 `fetch(limit)`，默认每维度 10 条 |
| L2 规则层 | `scripts/post_process.py` | 分源排序、URL 去重、标题相似合并；**不做跨源 hot_score 排序** |
| L3 Agent | `SKILL.md` | 按用户诉求精选条数、主题过滤、写总结 |

## 适配器约定

| 规则 | 说明 |
|------|------|
| 一平台一文件 | `scripts/adapters/{platform}_fetch.py` |
| 最热 + 最新 | 同一类 + `mode="hot"` / `mode="latest"` |
| 注册 | `main.py` 的 `ADAPTERS` 中，每个维度一行实例，并标注 `dimension`（`hot` / `latest`） |
| 数据模型 | `Article`（含 `to_dict()` 供 `--json` 输出） |

### 参考实现

- **双维度**：`juejinfetch.py`
- **双维度 + 可选密钥**：`douyin_fetch.py`（TikHub / 官方；未配置时返回空列表，不阻塞其他源）
- **单维度**：`qbitai_fetch.py`

## CLI

```bash
python main.py [--limit N] [--dimension all|hot|latest] [--json] [--push]
```

`--dimension`：注册表中每个 adapter 已标注 `hot` / `latest`；`hot` 只调各渠道热榜能力，`latest` 只调最新能力，`all` 为默认全量。

详细约束见 [prompt.md](../prompt.md) 与 [SKILL.md](../SKILL.md)。
