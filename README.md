# U1bot
> 欢迎大家pr，有任何问题可以提issue，代码写的很烂，欢迎大家指正，部分原创功能，部分为修改源代码，感谢大家的开源精神，太多无法列出，如有侵权请联系我删除。

## How to start

1. 安装 poetry `pip install poetry`
2. 安装依赖 `poetry install`
3. 运行 `poetry run python bot.py`

## 必填环境变量

1. QWEATHER_APIKEY: 和风天气的apikey，用于获取天气信息，[注册地址](https://dev.qweather.com/)
2. bilibili_cookie=xxx: B站用户cookie，用于获取用户信息，[获取方式](##cookie-获取方式)

## cookie-获取方式
需要在 `.env.xxx` 文件中添加任意的B站用户cookie：

```
bilibili_cookie=xxx
```

`cookie` 获取方式：

`F12` 打开开发工具，查看 `www.bilibili.com` 请求的响应头，找形如 `SESSDATA=xxx;` 的字段，如：

```
bilibili_cookie="SESSDATA=xxx;"
```

<div align="left">
  <img src="https://s2.loli.net/2022/07/19/AIBmd2Z9V5YwlkF.png" width="500" />
</div>
