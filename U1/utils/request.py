import httpx
from nonebot import logger as log
if timeout := 5:
    timeout = httpx.Timeout(timeout)
proxy = {}


async def get(url: str, **kwargs):
    log.debug(
        f"GET {url} by {proxy or 'No proxy'} | MORE: \n {kwargs}")
    async with httpx.AsyncClient(proxies=proxy, timeout=timeout) as client:  # type: ignore
        return await client.get(url, **kwargs)


async def post(url: str, **kwargs):
    log.debug(
        f"POST {url} by {proxy or 'No proxy'} | MORE: \n {kwargs}")
    async with httpx.AsyncClient(proxies=proxy, timeout=timeout) as client:  # type: ignore
        return await client.post(url, **kwargs)


async def delete(url: str, **kwargs):
    log.debug(
        f"DELETE {url} by {proxy or 'No proxy'} | MORE: \n {kwargs}")
    async with httpx.AsyncClient(proxies=proxy, timeout=timeout) as client:  # type: ignore
        return await client.delete(url, **kwargs)
