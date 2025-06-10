# game_server/Logic/InfrastructureLogic/DataAccessLogic/manager/generators/ORM_background_stories_manager.py

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert # Специфично для PostgreSQL

from game_server.database.models.models import BackgroundStory # Убедитесь, что импорт корректен

class BackgroundStoryManager:
    """
    Менеджер для управления объектами BackgroundStory в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_background_story_by_id(self, story_id: int) -> Optional[BackgroundStory]:
        """
        Получает предысторию по её ID.
        """
        stmt = select(BackgroundStory).where(BackgroundStory.story_id == story_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_background_story_by_name(self, name: str) -> Optional[BackgroundStory]:
        """
        Получает предысторию по её внутреннему названию.
        """
        stmt = select(BackgroundStory).where(BackgroundStory.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_background_stories(self) -> List[BackgroundStory]:
        """
        Возвращает все предыстории.
        """
        stmt = select(BackgroundStory)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert_background_story(self, story_data: Dict[str, Any]) -> BackgroundStory:
        """
        Создает или обновляет запись BackgroundStory, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Конфликт определяется по 'story_id' (если есть) или 'name'.
        """
        insert_stmt = pg_insert(BackgroundStory).values(**story_data)
        
        # Если story_id присутствует, используем его для upsert, иначе полагаемся на 'name'
        # Учитывая, что story_id SERIAL PRIMARY KEY, upsert по name более логичен
        # Если вы всегда будете передавать story_id для обновления, используйте index_elements=[BackgroundStory.story_id]
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[BackgroundStory.name], # Конфликт по уникальному имени
            set_={
                "display_name": insert_stmt.excluded.display_name,
                "short_description": insert_stmt.excluded.short_description,
                "stat_modifiers": insert_stmt.excluded.stat_modifiers,
                "skill_affinities": insert_stmt.excluded.skill_affinities,
                "initial_inventory_items": insert_stmt.excluded.initial_inventory_items,
                "starting_location_tags": insert_stmt.excluded.starting_location_tags,
                "lore_fragments": insert_stmt.excluded.lore_fragments,
                "potential_factions": insert_stmt.excluded.potential_factions,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
            }
        ).returning(BackgroundStory)

        result = await self.session.execute(on_conflict_stmt)
        await self.session.commit()
        return result.scalar_one()

    async def delete_background_story(self, story_id: int) -> bool:
        """
        Удаляет предысторию по её ID.
        """
        stmt = delete(BackgroundStory).where(BackgroundStory.story_id == story_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0