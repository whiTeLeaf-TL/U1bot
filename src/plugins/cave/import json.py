import json


class PluginMetadata:
    def __init__(self, name, description, usage, extra=None, **kwargs):
        self.name = name
        self.description = description
        self.usage = usage
        self.extra = extra or {}

        # 选择性地处理关键字参数
        for key in ["type", "homepage", "config"]:
            if key in kwargs:
                setattr(self, key, kwargs[key])
            else:
                setattr(self, key, None)


# 创建实例时提供额外的关键字参数
__plugin_meta__ = PluginMetadata(
    name="ph生成",
    description="生成pornhub风格图标",
    usage="ph生成 [文字1] [文字2]",
)
# 只保留特定的字段
metadata_dict = {
    "name": __plugin_meta__.name,
    "description": __plugin_meta__.description,
    "usage": __plugin_meta__.usage,
    "extra": __plugin_meta__.extra,
    # "type": __plugin_meta__.type,
    # "homepage": __plugin_meta__.homepage,
    # "config": __plugin_meta__.config,
}

# 转换为JSON格式
metadata_json = json.dumps(metadata_dict, ensure_ascii=False, indent=2)
print(metadata_json)
