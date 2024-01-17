# U1bot

U1bot 是一个XXX的项目，致力于XXX。欢迎大家贡献代码、提出问题或建议。本项目是基于开源精神构建的，感谢所有贡献者！


## 如何开始

1. 安装 poetry： `pip install poetry`
2. 安装依赖： `poetry install`
3. 运行： `poetry run python bot.py`


## 必填环境变量

1. `QWEATHER_APIKEY`：和风天气的 API Key，[注册地址](https://dev.qweather.com/)
2. `bilibili_cookie`：B站用户 Cookie，用于获取用户信息，[获取方式](#cookie-获取方式)


### Cookie 获取方式

1. 在 `.env.xxx` 文件中添加 B站用户 Cookie：

2. 获取 Cookie 的方式：

- 打开浏览器开发工具 `F12`
- 在开发者工具中查看 `www.bilibili.com` 请求的响应头
- 找到形如 `SESSDATA=xxx;` 的字段
- 复制整个字段，如下图所示：

<div align="left">
  <img src="https://s2.loli.net/2022/07/19/AIBmd2Z9V5YwlkF.png" width="500" />
</div>
