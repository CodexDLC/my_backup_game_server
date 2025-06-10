# game_server\Logic\ORM_LOGIC\managers\orm_Skillss.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import CharacterSkills, Skills










class CharacterSkillsManager:
    """Менеджер для работы с `character_skills` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_skill(self, character_id: int, skill_data: dict):
        """Добавление нового навыка персонажу."""
        skill = CharacterSkills(character_id=character_id, **skill_data)
        self.db_session.add(skill)
        await self.db_session.commit()
        return {"status": "success", "message": f"Навык `{skill_data['skill_key']}` добавлен персонажу `{character_id}`"}

    async def get_skill(self, character_id: int, skill_key: int):
        """Получение навыка персонажа."""
        query = select(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(query)
        skill = result.scalar()
        return {"status": "found", "data": skill.__dict__} if skill else {"status": "error", "message": "Навык не найден"}

    async def update_skill(self, character_id: int, skill_key: int, skill_data: dict):
        """Обновление навыка персонажа."""
        query = select(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(query)
        skill = result.scalar()

        if skill:
            for key, value in skill_data.items():
                setattr(skill, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Навык `{skill_key}` у персонажа `{character_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_skill(self, character_id: int, skill_key: int):
        """Удаление навыка персонажа."""
        query = select(CharacterSkills).where(
            CharacterSkills.character_id == character_id,
            CharacterSkills.skill_key == skill_key
        )
        result = await self.db_session.execute(query)
        skill = result.scalar()

        if skill:
            await self.db_session.delete(skill)
            await self.db_session.commit()
            return {"status": "success", "message": f"Навык `{skill_key}` у персонажа `{character_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
