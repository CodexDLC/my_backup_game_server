


import aiohttp
from Discord_API.discord_settings import API_URL


async def get_all_quests():
    """Получить список всех квестов."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/quests") as response:
            return await response.json()

async def create_quest(description_key: str, quest_data: dict):
    """Добавить новый квест."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/quests", json={"description_key": description_key, **quest_data}) as response:
            return await response.json()

async def get_quest(description_key: str):
    """Получить описание квеста по `description_key`."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/quests/{description_key}") as response:
            return await response.json()

async def update_quest(description_key: str, quest_data: dict):
    """Обновить описание квеста."""
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/quests/{description_key}", json=quest_data) as response:
            return await response.json()