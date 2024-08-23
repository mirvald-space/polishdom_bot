import asyncio

from aiohttp import ClientSession
from loguru import logger


async def keep_alive(webhook_url):
    base_url = webhook_url.rsplit('/', 1)[0]
    ping_url = f"{base_url}/ping"
    logger.info(f"Keep-alive function started with webhook URL: {webhook_url}")
    logger.info(f"Derived ping URL: {ping_url}")
    while True:
        logger.info("Attempting keep-alive request...")
        try:
            async with ClientSession() as session:
                async with session.get(ping_url) as response:
                    if response.status == 200:
                        text = await response.text()
                        if text == "pong":
                            logger.info("Keep-alive request successful")
                        else:
                            logger.warning(f"Unexpected response text: {text}")
                    else:
                        logger.warning(
                            f"Keep-alive request failed with status {response.status}")
        except Exception as e:
            logger.error(f"Keep-alive request encountered an error: {e}")
        logger.info("Waiting for next keep-alive request...")
        await asyncio.sleep(3600)
