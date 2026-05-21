"""深度思考路由插件。

纯插件实现，无需修改主程序代码：
1. 通过 maisaka.planner.before_request Hook 向 reply 工具注入 think_level 参数声明
2. 通过 maisaka.replyer.before_request Hook 拦截 replyer 请求，
   当 think_level >= 1 时指定深度思考模型并追加引导提示
"""

from typing import Any, Dict, List

from maibot_sdk import Field, HookHandler, MaiBotPlugin, PluginConfigBase
from maibot_sdk.types import HookMode, HookOrder


class PluginSectionConfig(PluginConfigBase):
    """插件基础配置。"""

    __ui_label__ = "插件"
    __ui_icon__ = "package"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="1.0.0", description="配置版本")


class DeepThinkConfig(PluginConfigBase):
    """深度思考配置。"""

    __ui_label__ = "深度思考"
    __ui_icon__ = "brain"
    __ui_order__ = 1

    model_name: str = Field(
        default="",
        description="深度思考时指定使用的模型名称（对应 model_config 中的 name 字段）。留空时使用默认 replyer 模型。",
    )
    extra_prompt: str = Field(
        default="当前回复需要更深入的思考。请仔细分析问题的各个方面，充分利用上下文和记忆信息，给出经过深思熟虑的回复。",
        description="深度思考模式下追加给 replyer 的额外提示词",
    )


class DeepThinkPluginConfig(PluginConfigBase):
    """深度思考路由插件配置。"""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    deep_think: DeepThinkConfig = Field(default_factory=DeepThinkConfig)


# reply 工具中注入的 think_level 参数定义
THINK_LEVEL_PARAM = {
    "think_level": {
        "type": "integer",
        "description": "思考深度。0=普通回复（默认）；1=当问题需要深度推理、逻辑分析、复杂计算或回忆大量上下文时使用，会启用深度思考模型生成更详细的回复。",
        "default": 0,
    }
}

# 追加到 reply 工具 description 末尾的引导文本
REPLY_DESCRIPTION_SUFFIX = "参数 think_level 可选：0=普通回复（默认），1=当问题需要深度推理、逻辑分析、复杂计算或回忆大量上下文时使用。"


class DeepThinkPlugin(MaiBotPlugin):
    """深度思考路由插件。"""

    config_model = DeepThinkPluginConfig

    async def on_load(self) -> None:
        """插件加载。"""

    async def on_unload(self) -> None:
        """插件卸载。"""

    async def on_config_update(self, scope: str, config_data: Dict[str, Any], version: str) -> None:
        """配置热更新。"""

    @HookHandler(
        "maisaka.planner.before_request",
        name="deep_think_inject_schema",
        description="向 reply 工具注入 think_level 参数声明",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
    )
    async def handle_planner_before_request(self, **kwargs: Any) -> Dict[str, Any]:
        """在 Planner 请求前，向 reply 工具的 parameters 中注入 think_level 并补充描述。"""

        tool_definitions: List[Dict[str, Any]] = kwargs.get("tool_definitions", [])
        if not isinstance(tool_definitions, list):
            return {}

        modified = False
        for tool_def in tool_definitions:
            if not isinstance(tool_def, dict):
                continue
            # 兼容 OpenAI function calling 格式
            func_info = tool_def.get("function", tool_def)
            if not isinstance(func_info, dict):
                continue
            if func_info.get("name") != "reply":
                continue

            # 注入 think_level 参数到 schema
            parameters = func_info.get("parameters")
            if isinstance(parameters, dict):
                properties = parameters.get("properties")
                if isinstance(properties, dict) and "think_level" not in properties:
                    properties.update(THINK_LEVEL_PARAM)
                    modified = True

            # 在工具描述中追加引导
            current_desc = str(func_info.get("description") or "")
            if "think_level" not in current_desc:
                func_info["description"] = f"{current_desc} {REPLY_DESCRIPTION_SUFFIX}".strip()
                modified = True
            break

        if modified:
            return {"tool_definitions": tool_definitions}
        return {}

    @HookHandler(
        "maisaka.replyer.before_request",
        name="deep_think_router",
        description="根据 think_level 切换 replyer 到深度思考模型",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
    )
    async def handle_replyer_before_request(self, **kwargs: Any) -> Dict[str, Any]:
        """在 replyer 请求前检查 think_level 并指定深度思考模型。"""

        reply_tool_args = kwargs.get("reply_tool_args", {})
        if not isinstance(reply_tool_args, dict):
            reply_tool_args = {}

        think_level = 0
        try:
            think_level = int(reply_tool_args.get("think_level", 0) or 0)
        except (TypeError, ValueError):
            pass

        if think_level < 1:
            return {}

        result: Dict[str, Any] = {}

        # 指定深度思考模型
        model_name = self.config.deep_think.model_name.strip()
        if model_name:
            result["model_name"] = model_name

        # 追加引导提示
        extra_prompt = self.config.deep_think.extra_prompt.strip()
        if extra_prompt:
            result["extra_prompt"] = extra_prompt

        return result


def create_plugin() -> DeepThinkPlugin:
    """插件入口工厂函数。"""
    return DeepThinkPlugin()
