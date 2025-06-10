# app/game_server/Logic/InterfacesLogic/Discord/Discord_State_Entities_logic.py


import uuid
from typing import Dict, Any, List # Добавляем List
from sqlalchemy.ext.asyncio import AsyncSession



from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.discord_api_route.ORM_EntitiesDiscord import StateEntitiesDiscordManager
from game_server.services.logging.logging_setup import logger


class StateEntitiesDiscordLogic:
    """
    Класс-мостик для обработки бизнес-логики, связывающей FastAPI роуты
    с CRUD-операциями StateEntitiesDiscordManager.
    Сессия базы данных внедряется через конструктор.
    """
    
    def __init__(self, db_session: AsyncSession): # 🔥🔥 ИЗМЕНЕНО: Добавляем __init__
        self.db_session = db_session
        self.manager = StateEntitiesDiscordManager(db_session) # Инициализируем менеджер здесь

    # ---------------------------------------------------------------------
    # Теперь все методы используют self.db_session и self.manager
    # УДАЛЯЕМ @staticmethod и вызовы async with get_db_session()
    # ---------------------------------------------------------------------

    async def get_all_entities_for_guild(self, guild_id: int) -> Dict:
        """
        Получить все записи из таблицы `state_entities_discord` для конкретной гильдии.
        """
        try:
            return await self.manager.get_all_entities_for_guild(guild_id) # Используем self.manager
        except Exception as e:
            logger.error(f"❌ Ошибка при получении всех сущностей для гильдии {guild_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка получения данных: {str(e)}"}

    async def get_entity_by_primary_key(self, guild_id: int, world_id: str, access_code: int) -> Dict:
        """
        Получить одну запись из таблицы `state_entities_discord` по первичному ключу.
        """
        try:
            try:
                world_id_val = uuid.UUID(world_id)
            except ValueError:
                logger.warning(f"⚠️ Некорректный формат world_id: {world_id}")
                return {"status": "error", "message": "Некорректный формат world_id"}

            return await self.manager.get_entity_by_pk(guild_id, world_id_val, access_code)
        except Exception as e:
            logger.error(f"❌ Ошибка при получении сущности по ПК (Guild: {guild_id}, World: {world_id}, Access: {access_code}): {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка получения данных: {str(e)}"}

    async def update_entity_by_primary_key(self, guild_id: int, world_id: str, access_code: int, entity_data: dict) -> Dict:
        """
        Обновить запись в таблице `state_entities_discord` по первичному ключу.
        """
        try:
            try:
                world_id_val = uuid.UUID(world_id)
            except ValueError:
                logger.warning(f"⚠️ Некорректный формат world_id для обновления: {world_id}")
                return {"status": "error", "message": "Некорректный формат world_id"}

            return await self.manager.update_entity_by_pk(guild_id, world_id_val, access_code, entity_data)
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении сущности по ПК (Guild: {guild_id}, World: {world_id}, Access: {access_code}): {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка обновления данных: {str(e)}"}

    async def delete_entity_by_primary_key(self, guild_id: int, world_id: str, access_code: int) -> Dict:
        """
        Удалить запись из таблицы `state_entities_discord` по первичному ключу.
        """
        try:
            try:
                world_id_val = uuid.UUID(world_id)
            except ValueError:
                logger.warning(f"⚠️ Некорректный формат world_id для удаления: {world_id}")
                return {"status": "error", "message": "Некорректный формат world_id"}

            return await self.manager.delete_entity_by_pk(guild_id, world_id_val, access_code)
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении сущности по ПК (Guild: {guild_id}, World: {world_id}, Access: {access_code}): {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка удаления данных: {str(e)}"}

    async def create_roles_discord(self, roles_batch: List[Dict]) -> Dict:
        """
        Массовое добавление/обновление записей `state_entities_discord` (UPSERT).
        """
        if not roles_batch or not all(isinstance(role, dict) for role in roles_batch):
            logger.warning("Некорректные данные, ожидался список словарей для create_roles_discord.")
            return {"error": "Некорректные данные, ожидался список словарей"}

        formatted_roles = []
        for role in roles_batch:
            try:
                guild_id_val = int(role["guild_id"])
                world_id_val = uuid.UUID(str(role["world_id"]))
                access_code_val = int(role["access_code"])

                other_fields = {k: v for k, v in role.items() if k not in ["guild_id", "world_id", "access_code"]}

                formatted_roles.append({
                    "guild_id": guild_id_val,
                    "world_id": world_id_val,
                    "access_code": access_code_val,
                    **other_fields
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"⚠️ Пропущена запись из-за некорректных данных при форматировании: {role}. Ошибка: {e}")
                continue

        if not formatted_roles:
            logger.warning("Нет корректно отформатированных данных о ролях для сохранения (create_roles_discord).")
            return {"error": "Нет корректно отформатированных данных о ролях для сохранения."}

        try:
            return await self.manager.create_roles_batch(formatted_roles)
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при массовом добавлении/обновлении ролей: {e}", exc_info=True)
            return {"error": f"Ошибка сохранения в БД: {str(e)}"}
