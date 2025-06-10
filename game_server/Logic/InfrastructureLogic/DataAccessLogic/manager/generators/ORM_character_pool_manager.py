

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert



from game_server.database.models.models import CharacterPool


class CharacterPoolRepository:
    """
    Репозиторий для выполнения асинхронных CRUD-операций над сущностью CharacterPool.
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает новую запись CharacterPool в базе данных.
        """
        # Удаляем character_pool_id из данных, если он там есть и равен None,
        # чтобы автоинкремент сработал корректно.
        # Или убеждаемся, что он не передается для новых записей.
        if 'character_pool_id' in character_data and character_data['character_pool_id'] is None:
            del character_data['character_pool_id']
            
        new_character = CharacterPool(**character_data)
        self.session.add(new_character)
        await self.session.flush() # Используем flush для получения ID перед commit
        await self.session.refresh(new_character) # Обновляем объект данными из БД (включая ID)
        # await self.session.commit() # Commit здесь не нужен, если flush + refresh достаточно
                                   # Обычно commit делается на более высоком уровне управления транзакцией.
                                   # Если этот метод должен быть атомарной операцией с commit, то раскомментируйте.
        return new_character

    async def upsert(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает или обновляет запись CharacterPool, используя upsert (INSERT ON CONFLICT DO UPDATE).
        """
        insert_stmt = pg_insert(CharacterPool).values(**character_data)

        # Поля для обновления в случае конфликта
        update_fields = {
            "name": insert_stmt.excluded.name,
            "surname": insert_stmt.excluded.surname,
            "gender": insert_stmt.excluded.gender,
            "base_stats": insert_stmt.excluded.base_stats,
            "initial_skill_levels": insert_stmt.excluded.initial_skill_levels,
            "creature_type_id": insert_stmt.excluded.creature_type_id,
            "personality_id": insert_stmt.excluded.personality_id,
            "background_story_id": insert_stmt.excluded.background_story_id,
            "initial_role_name": insert_stmt.excluded.initial_role_name,
            "visual_appearance_data": insert_stmt.excluded.visual_appearance_data,
            # 🔥🔥🔥 ИЗМЕНЕНИЕ ЗДЕСЬ: Меняем "initial_inventory" на "initial_inventory_id"
            "initial_inventory_id": insert_stmt.excluded.initial_inventory_id,
            "status": insert_stmt.excluded.status,
            "is_unique": insert_stmt.excluded.is_unique,
            "rarity_score": insert_stmt.excluded.rarity_score,
            "last_used_at": insert_stmt.excluded.last_used_at,
            "death_timestamp": insert_stmt.excluded.death_timestamp
        }
        # Добавляем last_accessed если оно есть в модели и должно обновляться
        if hasattr(insert_stmt.excluded, 'last_accessed'):
             update_fields["last_accessed"] = insert_stmt.excluded.last_accessed

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[CharacterPool.character_pool_id], # Конфликт по ID
            set_=update_fields
        ).returning(CharacterPool)

        result = await self.session.execute(on_conflict_stmt)
        updated_or_inserted_character = result.scalar_one()
        await self.session.flush()
        await self.session.refresh(updated_or_inserted_character)
        return updated_or_inserted_character


    async def get_by_id(self, character_pool_id: int) -> Optional[CharacterPool]:
        """
        Получает запись CharacterPool по её идентификатору.
        """
        stmt = select(CharacterPool).where(CharacterPool.character_pool_id == character_pool_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CharacterPool]:
        """
        Получает список записей CharacterPool с возможностью фильтрации, смещения и лимита.
        """
        stmt = select(CharacterPool)
        if filters:
            for key, value in filters.items():
                if hasattr(CharacterPool, key):
                    stmt = stmt.where(getattr(CharacterPool, key) == value)
        
        stmt = stmt.offset(offset).limit(limit).order_by(CharacterPool.character_pool_id) # Добавил order_by для консистентности
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, character_pool_id: int, update_data: Dict[str, Any]) -> Optional[CharacterPool]:
        """
        Обновляет запись CharacterPool по её идентификатору.
        """
        if not update_data: # Нечего обновлять
            return await self.get_by_id(character_pool_id)

        stmt = (
            update(CharacterPool)
            .where(CharacterPool.character_pool_id == character_pool_id)
            .values(**update_data)
            .returning(CharacterPool)
            .execution_options(synchronize_session="fetch") # или False, в зависимости от стратегии
        )
        result = await self.session.execute(stmt)
        updated_character = result.scalar_one_or_none()
        # await self.session.commit() # Commit обычно на уровне сервиса/use case
        if updated_character:
            await self.session.flush()
            await self.session.refresh(updated_character) # Обновить состояние объекта в сессии
        return updated_character

    async def delete(self, character_pool_id: int) -> bool:
        """
        Удаляет запись CharacterPool по её идентификатору.
        """
        stmt = delete(CharacterPool).where(CharacterPool.character_pool_id == character_pool_id)
        result = await self.session.execute(stmt)
        # await self.session.commit() # Commit обычно на уровне сервиса/use case
        return result.rowcount > 0

    # ---- НОВАЯ ФУНКЦИЯ ----
    async def get_all_characters(self) -> List[CharacterPool]:
        """
        Получает все записи из таблицы CharacterPool.

        Returns:
            List[CharacterPool]: Список всех объектов CharacterPool из базы данных.
        """
        stmt = select(CharacterPool).order_by(CharacterPool.character_pool_id) # Опционально: сортировка
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    # ---- КОНЕЦ НОВОЙ ФУНКЦИИ ----
