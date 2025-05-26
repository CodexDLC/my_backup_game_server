import aiohttp
from game_server.settings import API_URL  # Например, импорт из конфига

async def get_random_roll():
    """
    Получает случайное число из игрового пула через API.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("random_number")
            else:
                raise Exception(f"Ошибка запроса к API: {response.status}")
