
__all__ = ["request_open"]

import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def request_open(url):

    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'http://' + url)

    return html

