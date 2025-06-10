
#  /system/gameworld/


import aiohttp
from Discord_API.discord_settings import API_URL

BASE_PATH = "/system/gameworld"



async def get_current_world():
    """Получить текущий мир."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{BASE_PATH}/world") as response:
            print(f"🔍 Status: {response.status}")
            print(f"🔍 Headers: {response.headers}")
            print(f"🔍 Body: {await response.text()}")  # Посмотрим, что API реально возвращает
            return await response.json()

async def get_all_regions():
    """Получить все регионы."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{BASE_PATH}/regions") as response:
            return await response.json()

async def get_subregions():
    """Получить все подрегионы."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{BASE_PATH}/subregions") as response:
            return await response.json()



