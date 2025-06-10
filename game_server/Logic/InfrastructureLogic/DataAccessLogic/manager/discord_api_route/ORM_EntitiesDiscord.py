# game_server\Logic\ORM_LOGIC\managers\orm_discord_bindings.py
import datetime
from typing import List
import uuid
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import StateEntityDiscord
from game_server.services.logging.logging_setup import logger


class StateEntitiesDiscordManager:
    """Менеджер для работы с `state_entities_discord` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    # 1. Обновленный метод для массового создания/обновления ролей (UPSERT)
    async def create_roles_batch(self, roles_data: list[dict]) -> dict:
        """
        Массовое добавление/обновление записей в таблицу `state_entities_discord` (Upsert).
        Если запись с таким (guild_id, world_id, access_code) уже существует, она будет обновлена.
        """
        if not roles_data or not all(isinstance(data, dict) for data in roles_data):
            logger.warning("Некорректные данные для массовой вставки ролей: ожидался список словарей.")
            return {"status": "error", "message": "Некорректные данные, ожидался список словарей"}

        # SQLAlchemy сам преобразует dict в модель.
        # Если передаем role_id=None, и колонка nullable=True, то всё OK.
        roles_to_upsert = roles_data # Здесь roles_data уже отформатированы StateEntitiesDiscordLogic

        if not roles_to_upsert:
            logger.warning("После фильтрации не осталось корректных данных для вставки/обновления.")
            return {"status": "success", "message": "Нет данных для вставки/обновления."}

        try:
            # 🔥 ИСПОЛЬЗУЕМ ON CONFLICT DO UPDATE (UPSERT)
            stmt = insert(StateEntityDiscord).values(roles_to_upsert)
            
            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=['guild_id', 'world_id', 'access_code'], # По каким столбцам искать конфликт (ПК)
                set_={
                    'role_name': stmt.excluded.role_name, 
                    'role_id': stmt.excluded.role_id,     
                    'permissions': stmt.excluded.permissions, 
                    'updated_at': datetime.now(datetime.timezone.utc) 
                }
            )
            
            await self.db_session.execute(on_conflict_stmt)
            await self.db_session.commit()
            
            logger.info(f"✅ Успешно добавлено/обновлено {len(roles_to_upsert)} ролей в БД.")
            return {"status": "success", "message": f"Добавлено/обновлено {len(roles_to_upsert)} ролей"}
        except Exception as e:
            await self.db_session.rollback() 
            logger.error(f"❌ Ошибка сохранения/обновления ролей в БД: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка сохранения: {str(e)}"}

    # Метод create_entities_batch (если он был дубликатом) УДАЛЯЕТСЯ

    # Метод create_entity (для одной записи) остается, но возможно, его нужно будет использовать
    # с UPSERT, если он будет вызываться часто. Пока оставляем как есть, если это единичные вставки.
    async def create_entity(self, guild_id: int, entity_data: dict):
        """Добавление одной записи в таблицу `state_entities_discord`."""
        entity = StateEntityDiscord(guild_id=guild_id, **entity_data)
        try:
            self.db_session.add(entity)
            await self.db_session.commit()
            return {"status": "success", "message": f"Роль `{entity_data.get('role_name', 'N/A')}` добавлена для гильдии `{guild_id}`"}
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка добавления одной записи в БД: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка добавления: {str(e)}"}


    # 2. Обновленный метод для получения ВСЕХ записей по guild_id (для получения списка)
    async def get_all_entities_for_guild(self, guild_id: int):
        """Получение ВСЕХ записей для конкретного guild_id."""
        query = select(StateEntityDiscord).where(StateEntityDiscord.guild_id == guild_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()

        # Преобразуем SQLAlchemy объекты в чистые словари
        data = []
        for row in rows:
            row_dict = {
                "guild_id": row.guild_id,
                "world_id": str(row.world_id) if row.world_id else None, # Преобразовать UUID в строку
                "access_code": row.access_code,
                "role_name": row.role_name,
                "role_id": row.role_id,
                "permissions": row.permissions,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            data.append(row_dict)

        # 🔥 ИЗМЕНЕНИЕ ЗДЕСЬ: Возвращаем "found" и пустой список, если данных нет
        # или "not_found" если вы хотите явно указывать, что ничего не найдено,
        # но для "get_all" чаще всего возвращают пустой список и 200 OK.
        # Ваш роут уже обрабатывает "else: return []" как пустой список.
        # Поэтому достаточно вернуть status: "found" и пустой список.
        # Теперь возвращаем "found", если data не пуста, иначе "not_found"
        if data:
            return {"status": "found", "data": data}
        else:
            return {"status": "not_found", "data": []}


    # 3. Новые методы для работы с ОДНОЙ записью по ПЕРВИЧНОМУ КЛЮЧУ
    async def get_entity_by_pk(self, guild_id: int, world_id: uuid.UUID, access_code: int):
        """Получение одной записи по полному первичному ключу."""
        query = select(StateEntityDiscord).where(
            StateEntityDiscord.guild_id == guild_id,
            StateEntityDiscord.world_id == world_id,
            StateEntityDiscord.access_code == access_code
        )
        result = await self.db_session.execute(query)
        row = result.scalar_one_or_none()
        if row:
            row_dict = {
                "guild_id": row.guild_id,
                "world_id": str(row.world_id) if row.world_id else None,
                "access_code": row.access_code,
                "role_name": row.role_name,
                "role_id": row.role_id,
                "permissions": row.permissions,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            return {"status": "found", "data": row_dict}
        return {"status": "error", "message": "Запись не найдена"}

    async def update_entity_by_pk(self, guild_id: int, world_id: uuid.UUID, access_code: int, entity_data: dict):
        """Обновление одной записи по полному первичному ключу."""
        try:
            query = select(StateEntityDiscord).where(
                StateEntityDiscord.guild_id == guild_id,
                StateEntityDiscord.world_id == world_id,
                StateEntityDiscord.access_code == access_code
            )
            result = await self.db_session.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                for key, value in entity_data.items():
                    setattr(entity, key, value)
                await self.db_session.commit()
                return {"status": "success", "message": f"Запись для гильдии `{guild_id}` (World: {world_id}, Access: {access_code}) обновлена."}
            return {"status": "error", "message": "Запись не найдена"}
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка обновления записи по ПК: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка обновления: {str(e)}"}

    async def delete_entity_by_pk(self, guild_id: int, world_id: uuid.UUID, access_code: int):
        """Удаление одной записи по полному первичному ключу."""
        try:
            query = select(StateEntityDiscord).where(
                StateEntityDiscord.guild_id == guild_id,
                StateEntityDiscord.world_id == world_id,
                StateEntityDiscord.access_code == access_code
            )
            result = await self.db_session.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                await self.db_session.delete(entity)
                await self.db_session.commit()
                return {"status": "success", "message": f"Запись для гильдии `{guild_id}` (World: {world_id}, Access: {access_code}) удалена."}
            return {"status": "error", "message": "Запись не найдена"}
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка удаления записи по ПК: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка удаления: {str(e)}"}

    # 4. Добавленный метод для массового удаления по Discord role_id
    async def delete_roles_by_discord_ids(self, discord_role_ids: List[int]) -> dict:
        """
        Массовое удаление записей из таблицы `state_entities_discord` по `role_id`.
        Удаляет все записи, у которых `role_id` входит в переданный список.
        """
        if not discord_role_ids:
            logger.info("Нет ID ролей Discord для удаления из БД.")
            return {"status": "success", "message": "Нет ролей для удаления из БД."}

        try:
            stmt = delete(StateEntityDiscord).where(StateEntityDiscord.role_id.in_(discord_role_ids))
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            deleted_rows = result.rowcount
            logger.info(f"✅ Успешно удалено {deleted_rows} записей ролей из БД.")
            return {"status": "success", "message": f"Удалено {deleted_rows} записей ролей из БД."}
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка при массовом удалении ролей из БД по Discord ID: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка удаления из БД: {str(e)}"}
