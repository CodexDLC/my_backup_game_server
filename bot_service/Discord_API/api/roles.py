import os
import sys
import aiohttp
import logging

# 🔧 Добавление корня проекта в sys.path для корректного импорта модулей
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 🔗 Получение URL API
API_URL = os.getenv("GAME_SERVER_API", "http://localhost:8000")

from configs.logging_config import logger

logger = logging.getLogger(__name__)

# ---------------------- Получение информации о мире ----------------------
async def get_world_id():
    """ Запрос ID текущего игрового мира из API. """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/system/gameworld/world") as response:
            if response.status == 200:
                world_data = await response.json()
                logger.info(f"INFO Получен world_id: {world_data.get('id')}")
                return world_data.get("id")  
            else:
                logger.error("ERROR Ошибка при получении ID мира.")
                return None

# ---------------------- Получение списка ролей в гильдии ----------------------
async def get_existing_roles(guild_id: int):
    """ Запрашивает существующие роли в указанной гильдии. """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/discord/roles/list_roles/{guild_id}") as response:
            if response.status == 200:
                role_data = await response.json()
                roles = {role["access_code"] for role in role_data.get("roles", [])}
                logger.info(f"INFO Найдено {len(roles)} ролей для guild_id={guild_id}")
                return roles
            else:
                logger.error(f"ERROR Ошибка при проверке ролей (guild_id: {guild_id}).")
                return set()

# ---------------------- Получение доступных флагов ----------------------
async def get_available_flags():
    """ Запрашивает доступные состояния (флаги) в системе. """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/system/entities/available") as response:
            if response.status == 200:
                flag_data = await response.json()
                logger.info(f"INFO Получено {len(flag_data.get('flags', []))} флагов.")
                return flag_data.get("flags", [])
            else:
                logger.error("ERROR Ошибка при получении флагов.")
                return []

# ---------------------- Запись ролей в базу ----------------------
async def save_roles_to_db(guild_id: int, world_id: str, roles: list):
    """ Записывает список новых ролей в базу данных. """
    async with aiohttp.ClientSession() as session:
        payload = {"guild_id": guild_id, "world_id": world_id, "roles": roles}

        async with session.post(f"{API_URL}/discord/roles/create_roles", json=payload) as response:
            if response.status == 200:
                logger.info(f"INFO Записаны {len(roles)} новых ролей в базу (world_id={world_id}).")
            else:
                logger.error("ERROR Ошибка при записи ролей в API.")

# ---------------------- Удаление одной роли ----------------------
async def delete_role_from_db(guild_id: int, access_code: int):
    """ Удаляет одну роль по её access_code. """
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/discord/roles/delete_role/{guild_id}/{access_code}") as response:
            if response.status == 200:
                logger.info(f"🗑 Роль access_code={access_code} успешно удалена.")
                return await response.json()
            else:
                logger.error(f"ERROR Ошибка при удалении роли access_code={access_code}.")
                return {"status": "error"}

# ---------------------- Удаление всех ролей ----------------------
async def delete_all_roles_from_db(guild_id: int):
    """ Удаляет все роли в указанной гильдии. """
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/discord/roles/delete_all_roles/{guild_id}") as response:
            if response.status == 200:
                logger.info(f"🗑 Все роли для guild_id={guild_id} удалены.")
                return await response.json()
            else:
                logger.error(f"ERROR Ошибка при массовом удалении ролей в guild_id={guild_id}.")
                return {"status": "error"}
