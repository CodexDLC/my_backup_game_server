from typing import List, Dict, Optional, Any
from sqlalchemy import String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession # Импортируем AsyncSession

# Импортируем наш обновленный менеджер БД и его исключения

from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.discord_api_route.ORM_bindings_manager import BindingOperationError, DiscordBindingsManager
from game_server.database.models.models import DiscordBindings
from game_server.services.logging.logging_setup import logger


class DiscordBindingLogic:
    """
    Класс для управления привязками Discord-гильдий.
    Предоставляет логику более высокого уровня, используя DiscordBindingsManager.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_binding_by_key(self, guild_id: int, access_key: str) -> Optional[Dict[str, Any]]:
        """
        Получает одну привязку для гильдии по access_key.
        Возвращает данные привязки в виде словаря или None.
        """
        logger.info(f"Запрос привязки для guild_id={guild_id}, access_key={access_key}")
        manager = DiscordBindingsManager(self.db_session)
        try:
            binding = await manager.get_binding(guild_id, access_key)
            if binding:
                # Предполагаем, что у DiscordBindings есть метод .to_dict()
                # Если его нет, вам нужно будет вручную преобразовать ORM-объект в словарь.
                # Пример: return {"guild_id": binding.guild_id, "access_key": binding.access_key, ...}
                return binding.to_dict()
            return None
        except BindingOperationError as e:
            logger.error(f"Ошибка при получении привязки: {e}", exc_info=True)
            raise

    async def get_all_bindings(self, guild_id: Optional[int] = None) -> List[DiscordBindings]:
        """
        Получает все привязки или привязки для указанной гильдии,
        преобразуя BigInteger Discord ID в строки на уровне базы данных.
        Возвращает список объектов DiscordBindings ORM, с guild_id уже в виде строки.
        """
        logger.info(f"Запрос всех привязок для гильдии {guild_id if guild_id else 'всех гильдий'}")

        # 🔥🔥🔥 ЭТО И ЕСТЬ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: явное приведение типов в запросе SQLAlchemy 🔥🔥🔥
        # Мы явно выбираем все колонки и приводим guild_id к String
        query = select(
            cast(DiscordBindings.guild_id, String).label("guild_id"), # Преобразуем int/BigInteger в String
            DiscordBindings.world_id,
            DiscordBindings.access_key,
            DiscordBindings.permissions,
            DiscordBindings.created_at,
            DiscordBindings.updated_at,
            DiscordBindings.category_id,
            DiscordBindings.channel_id
        )

        if guild_id:
            # Важно: здесь, в фильтре, мы используем guild_id как число,
            # потому что в таблице базы данных оно все еще хранится как BigInteger.
            query = query.filter(DiscordBindings.guild_id == guild_id)

        try:
            result = await self.db_session.execute(query)
            
            # Поскольку мы использовали select с cast и label, result.scalars() не вернёт полные ORM-объекты.
            # result.all() вернёт список Row-объектов. Pydantic с from_attributes=True может работать с ними,
            # если имена колонок в запросе (с label) совпадают с именами полей в Pydantic-модели.
            all_rows = result.all() 
            
            logger.info(f"Получено {len(all_rows)} привязок для гильдии {guild_id}.")
            return all_rows # <-- Возвращаем список Row-объектов

        except Exception as e:
            logger.error(f"Ошибка при получении всех привязок: {e}", exc_info=True)
            # В данном случае, мы хотим, чтобы ошибка дошла до слоя API и была обработана FastAPI
            raise # Просто re-raise, если вы хотите, чтобы она была поймана выше
                  # Или можете обернуть её в BindingOperationError, как у вас было.

    async def upsert_discord_bindings(self, bindings_batch: List[Dict[str, Any]]) -> int:
        """
        Принимает список привязок и выполняет массовую вставку или обновление (UPSERT) в БД.
        Возвращает количество успешно обработанных записей.
        """
        logger.info(f"Попытка UPSERT для {len(bindings_batch)} привязок.")

        if not bindings_batch:
            logger.warning("`upsert_discord_bindings` вызвана с пустым списком данных.")
            return 0

        for binding in bindings_batch:
            if "guild_id" not in binding or "access_key" not in binding:
                logger.error(f"Пропущена привязка из-за отсутствия 'guild_id' или 'access_key': {binding}")
                raise ValueError("Каждая привязка должна содержать 'guild_id' и 'access_key'.")

        try:
            manager = DiscordBindingsManager(self.db_session)
            processed_count = await manager.upsert_bindings(bindings_batch)
            logger.info(f"Успешно обработано {processed_count} привязок через UPSERT.")
            return processed_count
        except BindingOperationError as e:
            logger.error(f"Ошибка при UPSERT привязок в БД: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка в `upsert_discord_bindings`: {e}", exc_info=True)
            raise

    async def delete_discord_binding(self, guild_id: int, access_key: str) -> bool:
        """
        Удаляет конкретную привязку Discord.
        Возвращает True при успешном удалении, False если не найдено.
        """
        logger.info(f"Попытка удаления привязки для guild_id={guild_id}, access_key={access_key}")
        manager = DiscordBindingsManager(self.db_session)
        try:
            result = await manager.delete_binding(guild_id, access_key)
            if result:
                logger.info(f"Привязка (guild_id={guild_id}, access_key={access_key}) успешно удалена.")
            else:
                logger.warning(f"Привязка (guild_id={guild_id}, access_key={access_key}) не найдена для удаления.")
            return result
        except BindingOperationError as e:
            logger.error(f"Ошибка при удалении привязки: {e}", exc_info=True)
            raise

    async def delete_all_discord_bindings_for_guild(self, guild_id: int) -> int:
        """
        Удаляет все привязки для указанной гильдии.
        Возвращает количество удаленных записей.
        """
        logger.info(f"Попытка удаления всех привязок для гильдии {guild_id}.")
        manager = DiscordBindingsManager(self.db_session)
        try:
            deleted_count = await manager.delete_all_bindings_for_guild(guild_id)
            logger.info(f"Удалено {deleted_count} привязок для гильдии {guild_id}.")
            return deleted_count
        except BindingOperationError as e:
            logger.error(f"Ошибка при удалении всех привязок для гильдии {guild_id}: {e}", exc_info=True)
            raise