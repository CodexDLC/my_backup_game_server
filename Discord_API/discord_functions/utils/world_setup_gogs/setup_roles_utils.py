
# Discord_API\discord_functions\utils\world_setup_gogs\setup_roles_utils.py

import asyncio
import uuid
from typing import Dict, List

import discord
from Discord_API.api_route_function.spec_route.state_entities_discord_api import get_all_entities_discord
from Discord_API.api_route_function.system.system_gameworld_api import get_current_world
from Discord_API.api_route_function.system.system_mapping_api import get_all_entities
from Discord_API.config.logging.logging_setup import logger







async def collect_roles():
    """Запрашивает данные из `state_entities`, формирует JSON со структурированными ролями."""

    logger.info("🛠 Запрос `state_entities` для получения ролей...")
    
    # Получаем данные из get_all_entities.
    # Ожидаем формат: {"roles": [...]}
    api_response_data = await get_all_entities()

    # 🔥 Проверки API-ответа, который мы получили от get_all_entities()
    # Эта функция теперь должна возвращать {"roles": [...]}
    if not isinstance(api_response_data, dict) or "roles" not in api_response_data:
        logger.warning(
            f"⚠️ Неожиданный формат данных от `get_all_entities()`. "
            f"Ожидали dict с ключом 'roles', получили: {api_response_data}"
        )
        return {"roles": []}

    # Теперь мы знаем, что api_response_data это {"roles": [...]}, 
    # и мы можем безопасно извлечь список сущностей
    all_states_list = api_response_data["roles"]

    if not isinstance(all_states_list, list):
        logger.error(f"❌ Ошибка! `all_states_list` должен быть списком, но получен {type(all_states_list)}. Возвращаем `roles: []`.")
        return {"roles": []}
    
    # Фильтрация только активных состояний
    active_states = [state for state in all_states_list if state.get("is_active", False)]

    # 📌 Формируем структуру данных для Discord-ролей
    roles_data = {
        "roles": [
            {
                "guild_id": None,   # Пока None, будет заполняться позже
                "access_code": state.get("access_code"),
                "role_name": state.get("code_name"),
                "role_id": None,    # Пока None, будет заполняться после создания роли в Discord
                "permissions": 0,   # По умолчанию 0, возможно, нужно будет настроить
                "ui_type": state.get("ui_type"),
                "description": state.get("description"),
                "is_active": state.get("is_active", False)
            }
            for state in active_states
        ]
    }

    logger.info(f"✅ Успешно сформирован `roles_data`: {roles_data}")

    return roles_data





async def collect_roles_discord(guild_id: int):
    """Вызывает API через `get_all_entities_discord()`, получает роли и формирует список."""

    if guild_id is None:
        logger.error("❌ Некорректный `guild_id`, отмена запроса")
        return []

    logger.info(f"🛠 Запрос ролей Discord для `guild_id={guild_id}`...")
    roles_discord = await get_all_entities_discord(guild_id)

    # --- ИСПРАВЛЕННАЯ ЛОГИКА ПРОВЕРКИ И ФОРМИРОВАНИЯ ---
    # 🔥 Проверяем ответ API
    # Если roles_discord не является списком, это ошибка
    if not isinstance(roles_discord, list):
        logger.error(f"❌ Ожидался список ролей из API, но получен другой тип: {type(roles_discord).__name__}. API-ответ: {roles_discord}")
        return []
    
    # Если список пуст, это не ошибка, а просто нет ролей для обработки
    if not roles_discord:
        logger.warning(f"⚠️ Нет данных о ролях в Discord! API-ответ: {roles_discord}")
        return [] 
    # --- КОНЕЦ ИСПРАВЛЕННОЙ ЛОГИКИ ПРОВЕРКИ ---

    logger.info(f"✅ Полученные роли из Discord API: {roles_discord}")

    # 📌 Формируем список ролей
    roles_list = [
        {
            "guild_id": role["guild_id"],
            "world_id": role["world_id"],
            "access_code": role["access_code"],
            "role_name": role["role_name"],
            "role_id": role["role_id"],
            "permissions": role["permissions"]
        }
        for role in roles_discord # ✨ ИЗМЕНЕНО: Итерируем напрямую по roles_discord
    ]

    logger.info(f"✅ Сформирован `roles_list`: {roles_list}")

    return roles_list



async def find_missing_roles(guild_id: int):
    """Определяет, какие роли нужно создать, либо создаёт все роли, если гильдии нет."""

    if guild_id is None:
        print("❌ Некорректный `guild_id`, отмена запроса")
        return []

    print(f"🛠 Запрос существующих ролей в гильдии `{guild_id}`...")
    roles_list = await collect_roles_discord(guild_id)  # 🔥 Теперь это `roles_list` из `collect_roles_discord()`

    print(f"🔍 Получены существующие роли: {roles_list}")

    print("🛠 Запрос всех доступных ролей...")
    roles_data = await collect_roles()
    print(f"🔍 Полный список доступных ролей: {roles_data.get('roles', [])}")

    # 🔥 Если `roles_list` пуст — создаём ВСЕ роли
    if not roles_list:
        print(f"⚠️ Гильдия `{guild_id}` не найдена! Создаём ВСЕ роли.")
        missing_roles = roles_data.get("roles", [])  # ✅ Заполняем ВСЕ роли
    else:
        # 📌 Если гильдия найдена — сравниваем списки и создаём только отсутствующие роли
        existing_roles = {role["access_code"]: role.get("access_code") for role in roles_list}
        missing_roles = [
            role for role in roles_data.get("roles", [])
            if role["access_code"] not in existing_roles
        ]

    print(f"🔍 Сформирован список отсутствующих ролей: {missing_roles}")

    return missing_roles







async def build_roles_batch(roles_bindings: List[Dict]) -> List[Dict]:
    """Собирает пакет данных для массовой вставки ролей, включая `guild_id`, `world_id` и `access_code`."""

    current_world = await get_current_world()
    world_id = current_world.get("world_id") if current_world else str(uuid.uuid4())  # ✅ Если `world_id` отсутствует, генерируем новый

    return [
        {
            "guild_id": role["guild_id"],
            "world_id": world_id,  # ✅ Теперь `world_id` получаем из API или создаем
            "access_code": role.get("access_code", "UNKNOWN"),
            "role_name": role.get("role_name"),
            "role_id": role.get("role_id"),
            "permissions": role.get("permissions", 0)
        }
        for role in roles_bindings if role.get("access_code")
    ]


async def fetch_actual_guild_roles(guild: discord.Guild) -> List[discord.Role]:
    """
    Получает актуальный список ролей с сервера Discord.
    Обрабатывает возможные ошибки API.
    """
    try:
        current_discord_roles = await guild.fetch_roles()
        logger.info(f"🔄 Получен актуальный список из {len(current_discord_roles)} ролей с сервера '{guild.name}' ({guild.id}).")
        return current_discord_roles
    except discord.HTTPException as e:
        logger.error(f"❌ Ошибка API при получении ролей с Discord (статус: {e.status}, текст: {e.text}).", exc_info=True)
        return [] # Возвращаем пустой список, если не удалось получить
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении ролей с Discord: {e}", exc_info=True)
        return []
    

async def send_and_delete_temp_message(channel: discord.TextChannel, content: str, delay_seconds: int = 120):
    """Отправляет сообщение в канал и планирует его удаление через заданное время."""
    if not channel:
        logger.warning("⚠️ Попытка отправить временное сообщение в None-канал.")
        return

    try:
        message = await channel.send(content)
        asyncio.create_task(message.delete(delay=delay_seconds))
        logger.debug(f"Сообщение '{content[:30]}...' отправлено в '{channel.name}' и будет удалено через {delay_seconds}с.")
    except discord.HTTPException as e:
        logger.error(f"❌ Не удалось отправить/удалить временное сообщение в канал '{channel.name}': {e.status} - {e.text}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при отправке временного сообщения: {e}", exc_info=True)




async def save_roles_bindings_to_db(guild_id: int, bindings: List[Dict]):
    """
    Заглушка: Сохраняет или обновляет привязки ролей в базе данных.
    Здесь должна быть ваша реальная логика работы с БД.
    """
    if not bindings:
        logger.info(f"💾 Нет привязок для сохранения в БД для гильдии {guild_id}.")
        return

    logger.info(f"💾 Сохраняем/обновляем {len(bindings)} привязок ролей в БД для гильдии {guild_id}...")
    # Здесь должна быть ваша реальная логика работы с БД,
    # например, вставка или обновление записей в таблице role_bindings
    # Пример (псевдокод):
    # for binding in bindings:
    #     await db_session.merge(RoleBindingModel(**binding))
    # await db_session.commit()
    logger.info(f"✅ Сохранение привязок ролей в БД завершено.")