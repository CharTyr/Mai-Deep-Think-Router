# Mai-Deep-Think-Router

MaiBot 深度思考路由插件。当 Planner 判定问题需要深度推理时，自动切换到指定的思考模型进行回复。

## 安装

将本仓库克隆到 MaiBot 的 `plugins/` 目录下：

```bash
cd plugins/
git clone https://github.com/CharTyr/Mai-Deep-Think-Router.git deep_think_plugin
```

重启 MaiBot 即可。

## 配置

插件加载后会在 `plugins/deep_think_plugin/` 下生成 `config.toml`，也可在 WebUI 插件配置页修改。

关键配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `deep_think.model_name` | 深度思考时使用的模型名称，对应 `model_config.toml` 中 `[[models]]` 的 `name` 字段 | 空（不生效） |
| `deep_think.extra_prompt` | 深度思考模式下追加给回复器的引导提示词 | 见下方 |

默认引导提示词：
> 当前回复需要更深入的思考。请仔细分析问题的各个方面，充分利用上下文和记忆信息，给出经过深思熟虑的回复。

### 配置示例

假设你的 `model_config.toml` 中有如下模型定义：

```toml
[[models]]
name = "deepseek-v4-pro-thinking"
model_identifier = "deepseek-v4-pro"
api_provider = "DeepSeek"
extra_params = { thinking = { type = "enabled" } }
```

则在插件配置中填写：

```toml
[deep_think]
model_name = "deepseek-v4-pro-thinking"
```

## 工作原理

1. **Planner 阶段** — 插件通过 `maisaka.planner.before_request` Hook 向 reply 工具动态注入 `think_level` 参数，Planner 会在需要深度推理时传入 `think_level=1`
2. **Replyer 阶段** — 插件通过 `maisaka.replyer.before_request` Hook 拦截请求，当检测到 `think_level=1` 时，将模型切换为配置中指定的思考模型，并追加引导提示词

整个过程不修改主程序代码，完全通过 Hook 机制实现。

## 要求

- MaiBot >= 1.0.0（需支持 `maisaka.replyer.before_request` Hook）
- maibot-plugin-sdk >= 2.0.0

## 许可证

GPL-3.0-or-later
