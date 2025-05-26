# game_server\Logic\ORM_LOGIC\managers\orm_Skillss.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import CharacterSkills, Skills

class SkillManager:
    """Менеджер для работы с `Skillss` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_Skills(self, Skills_data: dict):
        """Добавление нового навыка."""
        Skills = Skills(**Skills_data)
        self.db_session.add(Skills)
        await self.db_session.commit()
        return {"status": "success", "message": f"Навык `{Skills_data['name']}` добавлен"}

    async def get_Skillss(self, Skills_id: int = None, Skills_key: str = None, Skills_group: str = None):
        """Получение списка навыков по переданным параметрам."""
        query = select(Skills)

        if Skills_id:
            query = query.where(Skills.Skills_id == Skills_id)
        if Skills_key:
            query = query.where(Skills.Skills_key == Skills_key)
        if Skills_group:
            query = query.where(Skills.Skills_group == Skills_group)

        result = await self.db_session.execute(query)
        rows = result.scalars().all()

        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Навыки не найдены"}

    async def update_Skills(self, Skills_id: int, Skills_data: dict):
        """Обновление данных навыка."""
        query = select(Skills).where(Skills.Skills_id == Skills_id)
        result = await self.db_session.execute(query)
        Skills = result.scalar()

        if Skills:
            for key, value in Skills_data.items():
                setattr(Skills, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Навык `{Skills_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_Skills(self, Skills_id: int):
        """Удаление навыка."""
        query = select(Skills).where(Skills.Skills_id == Skills_id)
        result = await self.db_session.execute(query)
        Skills = result.scalar()

        if Skills:
            await self.db_session.delete(Skills)
            await self.db_session.commit()
            return {"status": "success", "message": f"Навык `{Skills_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}




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
