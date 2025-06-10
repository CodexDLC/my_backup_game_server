from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Personality


class PersonalityManager:
    """
    Менеджер для управления объектами Personality в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session # self.session уже корректно инициализирована

    async def get_personality_by_id(self, personality_id: int) -> Optional[Personality]:
        """Получает личность по её ID."""
        stmt = select(Personality).where(Personality.personality_id == personality_id)
        result = await self.session.execute(stmt) # ИСПРАВЛЕНО: self.db на self.session
        return result.scalar_one_or_none()

    async def get_personality_by_name(self, name: str) -> Optional[Personality]:
        """Получает личность по её названию."""
        stmt = select(Personality).where(Personality.name == name)
        result = await self.session.execute(stmt) # ИСПРАВЛЕНО: self.db на self.session
        return result.scalar_one_or_none()

    async def get_all_personalities(self) -> List[Personality]:
        """Возвращает все личности."""
        stmt = select(Personality)
        result = await self.session.execute(stmt) # ИСПРАВЛЕНО: self.db на self.session
        return result.scalars().all()

    async def upsert_personality(self, personality_data: Dict[str, Any]) -> Personality:
        """
        Создает или обновляет запись Personality, используя upsert (INSERT ON CONFLICT DO UPDATE).

        Args:
            personality_data (Dict[str, Any]): Словарь с данными для создания/обновления личности.
                                                Должен содержать 'personality_id' для идентификации.

        Returns:
            Personality: Созданный или обновленный объект Personality.
        """
        insert_stmt = pg_insert(Personality).values(**personality_data)
        
        # Определяем, какие поля обновлять в случае конфликта (по personality_id)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Personality.personality_id], # По каким полям определяем конфликт
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description,
                "personality_group": insert_stmt.excluded.personality_group,
                "behavior_tags": insert_stmt.excluded.behavior_tags,
                "dialogue_modifiers": insert_stmt.excluded.dialogue_modifiers,
                "combat_ai_directives": insert_stmt.excluded.combat_ai_directives,
                "quest_interaction_preferences": insert_stmt.excluded.quest_interaction_preferences,
                "trait_associations": insert_stmt.excluded.trait_associations,
                "applicable_game_roles": insert_stmt.excluded.applicable_game_roles,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
                "ai_priority_level": insert_stmt.excluded.ai_priority_level,
                # Добавьте все поля, которые вы хотите обновлять
            }
        ).returning(Personality) # Возвращаем объект после upsert

        result = await self.session.execute(on_conflict_stmt) # ИСПРАВЛЕНО: self.db на self.session
        await self.session.commit() # ИСПРАВЛЕНО: self.db на self.session
        
        return result.scalar_one() # Используем scalar_one, так как upsert всегда возвращает одну строку

    async def delete_personality(self, personality_id: int) -> bool:
        """
        Удаляет личность по её ID.
        Использует delete-statement для более эффективного удаления.
        """
        stmt = delete(Personality).where(Personality.personality_id == personality_id)
        result = await self.session.execute(stmt) # ИСПРАВЛЕНО: self.db на self.session
        await self.session.commit() # ИСПРАВЛЕНО: self.db на self.session
        return result.rowcount > 0 # Возвращаем True, если была удалена хотя бы одна строка