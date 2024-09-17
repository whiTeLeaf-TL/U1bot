import aiohttp

from .config import Config


async def chat_with_gpt(data: list, config: Config) -> str:
    payload = {
        "messages": data,
        "model": config.appoint_model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            config.base_url + "/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        ) as resp:
            result = await resp.json()
            return result["choices"][0]["message"]["content"]
