
from typing import List, Dict, Optional, Any
from sqlalchemy.dialects.postgresql import insert as sa_insert # <-- ЭТОТ ИМПОРТ ИСПОЛЬЗУЙТЕ!
from sqlalchemy import delete, func, select, text, BigInteger, String, Integer, DateTime, Uuid # <-- УДАЛИТЕ 'insert' ОТСЮДА!
from sqlalchemy.dialects import postgresql # Важно для ON CONFLICT DO UPDATE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import PrimaryKeyConstraint # Для явного определения PK в модели (если если нет в models.py)

# Предполагаем, что DiscordBindings импортируется из вашего файла моделей
from game_server.database.models.models import DiscordBindings
from game_server.services.logging.logging_setup import logger # Ваш настроенный логгер

# Кастомные исключения для более явной обработки ошибок
class BindingNotFoundError(Exception):
    """Исключение: привязка не найдена."""
    pass

class BindingOperationError(Exception):
    """Базовое исключение для ошибок операций с привязками к БД."""
    pass

class DiscordBindingsManager:
    """
    Менеджер для работы с таблицей `discord_bindings` через SQLAlchemy ORM.
    Предполагает, что используемая БД поддерживает UPSERT (например, PostgreSQL).
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_binding(self, guild_id: int, access_key: str) -> Optional[DiscordBindings]:
        """
        Получает привязку по guild_id и access_key.
        Возвращает объект `DiscordBindings` или `None`, если привязка не найдена.
        """
        try:
            query = select(DiscordBindings).where(
                DiscordBindings.guild_id == guild_id,
                DiscordBindings.access_key == access_key
            )
            result = await self.db_session.execute(query)
            binding = result.scalar_one_or_none()
            return binding
        except Exception as e:
            logger.error(f"Ошибка при получении привязки (guild_id={guild_id}, access_key={access_key}): {e}", exc_info=True)
            raise BindingOperationError(f"Не удалось получить привязку.") from e

    async def get_all_bindings(self, guild_id: Optional[int] = None) -> List[DiscordBindings]:
        """
        Получает все привязки или привязки для конкретной гильдии.

        Args:
            guild_id (Optional[int]): Если указан, возвращает привязки только для этой гильдии.
                                      Если None, возвращает все привязки.

        Returns:
            List[DiscordBindings]: Список объектов `DiscordBindings`.

        Raises:
            BindingOperationError: Если произошла ошибка при работе с базой данных.
        """
        try:
            query = select(DiscordBindings)
            if guild_id is not None:
                query = query.where(DiscordBindings.guild_id == guild_id)

            result = await self.db_session.execute(query)
            bindings = result.scalars().all()
            logger.info(f"Получено {len(bindings)} привязок для гильдии {guild_id if guild_id else 'всех гильдий'}.")
            return bindings
        except Exception as e:
            logger.error(f"Ошибка при получении всех привязок (guild_id={guild_id}): {e}", exc_info=True)
            raise BindingOperationError(f"Не удалось получить все привязки.") from e

    async def delete_binding(self, guild_id: int, access_key: str) -> bool:
        """
        Удаляет привязку по guild_id и access_key.
        Возвращает `True` при успешном удалении, `False` если запись не найдена.
        Выбрасывает `BindingOperationError` при других ошибках базы данных.
        """
        try:
            binding_to_delete = await self.get_binding(guild_id, access_key) # Используем get_binding
            if binding_to_delete:
                await self.db_session.delete(binding_to_delete)
                await self.db_session.commit()
                logger.info(f"Привязка (guild_id={guild_id}, access_key={access_key}) успешно удалена.")
                return True
            else:
                logger.warning(f"Попытка удалить несуществующую привязку (guild_id={guild_id}, access_key={access_key}).")
                return False
        except Exception as e:
            await self.db_session.rollback() # Откатываем транзакцию в случае ошибки
            logger.error(f"Ошибка при удалении привязки (guild_id={guild_id}, access_key={access_key}): {e}", exc_info=True)
            raise BindingOperationError(f"Ошибка при удалении привязки.") from e

    async def upsert_bindings(self, bindings_data: List[Dict[str, Any]]) -> int:
        """
        Массовая вставка или обновление привязок (`UPSERT`) в таблице `discord_bindings`.
        Использует `ON CONFLICT DO UPDATE` для PostgreSQL.
        """
        if not bindings_data:
            logger.warning("`upsert_bindings` вызвана с пустым списком данных.")
            return 0

        # Statement для UPSERT: сначала создаем insert_stmt
        insert_stmt = sa_insert(DiscordBindings).values(bindings_data)

        # Теперь определяем поля для обновления, используя insert_stmt.excluded
        update_cols = {
            'world_id': insert_stmt.excluded.world_id, # <--- ИСПРАВЛЕНО
            'permissions': insert_stmt.excluded.permissions,
            'category_id': insert_stmt.excluded.category_id,
            'channel_id': insert_stmt.excluded.channel_id,
            'updated_at': func.now() # Используем func.now() из SQLAlchemy для консистентности
        }

        # ON CONFLICT ON CONSTRAINT discord_bindings_pkey (или ON CONFLICT (guild_id, access_key))
        # DO UPDATE SET ...
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['guild_id', 'access_key'], # По этим полям определяется конфликт
            set_=update_cols # Что обновляем при конфликте
        )

        try:
            result = await self.db_session.execute(on_conflict_stmt)
            await self.db_session.commit()
            
            # Количество строк, для которых была предпринята попытка UPSERT
            # Если вам нужно точное количество вставленных/обновленных, это сложнее
            processed_rows = len(bindings_data) # Или result.rowcount, но он может быть неточным для upsert
            
            logger.info(f"Успешно выполнен UPSERT для {processed_rows} привязок.")
            return processed_rows
            
        except Exception as e:
            await self.db_session.rollback() # Откатываем транзакцию в случае ошибки
            logger.error(f"Ошибка при массовом UPSERT привязок: {e}", exc_info=True)
            # Убедитесь, что BindingOperationError импортирована
            raise BindingOperationError(f"Ошибка при массовом UPSERT привязок: {e}") from e

    async def delete_all_bindings_for_guild(self, guild_id: int) -> int:
        """
        Удаляет все привязки для указанной гильдии.
        Возвращает количество удаленных записей.
        Выбрасывает BindingOperationError при ошибках БД.
        """
        try:
            stmt = delete(DiscordBindings).where(DiscordBindings.guild_id == guild_id)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            logger.info(f"Удалено {result.rowcount} привязок для гильдии {guild_id}.")
            return result.rowcount
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка при массовом удалении привязок для гильдии {guild_id}: {e}", exc_info=True)
            raise BindingOperationError(f"Ошибка при массовом удалении привязок для гильдии {guild_id}.") from e