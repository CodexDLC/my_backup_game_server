# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\generators\data\ORM_creature_type_manager.py


from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update # Добавил insert
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert # Специфично для PostgreSQL

from game_server.database.models.models import CreatureType, CreatureTypeInitialSkill # Для загрузки связанных данных



class CreatureTypeManager: # Имя класса, которое вы используете
    """
    Менеджер для управления объектами CreatureType в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session # Переименовал self.db на self.session

    async def get_creature_type_by_id(self, creature_type_id: int) -> Optional[CreatureType]:
        """
        Получает определение типа существа по его ID.
        """
        stmt = select(CreatureType).where(CreatureType.creature_type_id == creature_type_id)
        result = await self.session.execute(stmt) # Использовал self.session
        return result.scalar_one_or_none()

    async def get_creature_type_by_name(self, name: str) -> Optional[CreatureType]:
        """
        Получает тип существа по его имени (name).
        """
        stmt = select(CreatureType).where(CreatureType.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_creature_types(self) -> List[CreatureType]:
        """
        Возвращает все типы существ.
        """
        stmt = select(CreatureType)
        result = await self.session.execute(stmt) # Использовал self.session
        return result.scalars().all()

    async def get_filtered_by_category_and_playable(self, category: str, is_playable: bool) -> List[CreatureType]:
        """
        Получает отфильтрованные типы существ по категории и флагу is_playable.
        Этот метод будет использоваться генератором.
        """
        stmt = select(CreatureType).where(
            CreatureType.category == category,
            CreatureType.is_playable == is_playable
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_creature_type(self, data: Dict[str, Any]) -> CreatureType:
        """
        Создает новый тип существа.
        data: Словарь с данными для создания CreatureType (например, {'creature_type_id': 1, 'name': 'Human', ...}).
        """
        new_creature_type = CreatureType(**data)
        self.session.add(new_creature_type)
        await self.session.flush()
        return new_creature_type

    async def update_creature_type(self, creature_type_id: int, data: Dict[str, Any]) -> Optional[CreatureType]:
        """
        Обновляет существующий тип существа по ID.
        data: Словарь с полями для обновления.
        """
        stmt = update(CreatureType).where(CreatureType.creature_type_id == creature_type_id).values(**data).returning(CreatureType)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_creature_type(self, creature_type_data: Dict[str, Any]) -> CreatureType:
        """
        Создает или обновляет тип существа в базе данных, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Args:
            creature_type_data (Dict[str, Any]): Словарь с данными для типа существа.
                                                  Должен содержать 'creature_type_id' для идентификации.
        Returns:
            CreatureType: Созданный или обновленный объект CreatureType.
        """
        insert_stmt = pg_insert(CreatureType).values(**creature_type_data)

        # Определяем, какие поля обновлять в случае конфликта (по creature_type_id)
        # Исключаем 'creature_type_id' из set_, так как это PK
        update_cols = {k: insert_stmt.excluded[k] for k in creature_type_data if k != 'creature_type_id'}

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[CreatureType.creature_type_id],
            set_=update_cols
        ).returning(CreatureType)

        result = await self.session.execute(on_conflict_stmt)
        return result.scalar_one()

    async def delete_creature_type(self, creature_type_id: int) -> bool:
        """
        Удаляет тип существа по его ID.
        Использует delete-statement для более эффективного удаления.
        """
        stmt = delete(CreatureType).where(CreatureType.creature_type_id == creature_type_id).returning(CreatureType.creature_type_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_creature_type_with_initial_skills(self, creature_type_id: int) -> Optional[CreatureType]:
        """
        Получает тип существа вместе с его начальными навыками.
        Использует selectinload для оптимизированной загрузки связанных данных.
        """
        stmt = select(CreatureType).where(CreatureType.creature_type_id == creature_type_id).options(
            selectinload(CreatureType.initial_skills).selectinload(CreatureTypeInitialSkill.skill_definition)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()