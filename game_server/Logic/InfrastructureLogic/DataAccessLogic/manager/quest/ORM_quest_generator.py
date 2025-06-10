from sqlalchemy import select

from game_server.Logic.DataAccessLogic.db_instance import AsyncSession
from game_server.database.models.models import QuestConditions, QuestRequirements, QuestRewards, QuestTemplatesMaster, QuestTypes

class QuestTemplatesMasterManager:
    """Менеджер для работы с `quest_templates_master` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_template(self, template_id: int, quest_data: dict):
        """Добавление нового шаблона квеста."""
        template = QuestTemplatesMaster(template_id=template_id, **quest_data)
        self.db_session.add(template)
        await self.db_session.commit()
        return {"status": "success", "message": f"Шаблон `{quest_data['template_key']}` добавлен"}

    async def get_template(self, template_id: int):
        """Получение шаблона квеста по ID."""
        query = select(QuestTemplatesMaster).where(QuestTemplatesMaster.template_id == template_id)
        result = await self.db_session.execute(query)
        template = result.scalar()
        return {"status": "found", "data": template.__dict__} if template else {"status": "error", "message": "Шаблон не найден"}

    async def update_template(self, template_id: int, quest_data: dict):
        """Обновление шаблона квеста."""
        query = select(QuestTemplatesMaster).where(QuestTemplatesMaster.template_id == template_id)
        result = await self.db_session.execute(query)
        template = result.scalar()

        if template:
            for key, value in quest_data.items():
                setattr(template, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Шаблон `{template_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_template(self, template_id: int):
        """Удаление шаблона квеста."""
        query = select(QuestTemplatesMaster).where(QuestTemplatesMaster.template_id == template_id)
        result = await self.db_session.execute(query)
        template = result.scalar()

        if template:
            await self.db_session.delete(template)
            await self.db_session.commit()
            return {"status": "success", "message": f"Шаблон `{template_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
    

class QuestTypesManager:
    """Менеджер для работы с `quest_types` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_quest_type(self, type_id: int, type_data: dict):
        """Добавление нового типа квеста."""
        quest_type = QuestTypes(type_id=type_id, **type_data)
        self.db_session.add(quest_type)
        await self.db_session.commit()
        return {"status": "success", "message": f"Тип `{type_data['type_name']}` добавлен"}

    async def get_quest_type(self, type_id: int):
        """Получение типа квеста по ID."""
        query = select(QuestTypes).where(QuestTypes.type_id == type_id)
        result = await self.db_session.execute(query)
        quest_type = result.scalar()
        return {"status": "found", "data": quest_type.__dict__} if quest_type else {"status": "error", "message": "Тип квеста не найден"}

    async def update_quest_type(self, type_id: int, type_data: dict):
        """Обновление типа квеста."""
        query = select(QuestTypes).where(QuestTypes.type_id == type_id)
        result = await self.db_session.execute(query)
        quest_type = result.scalar()

        if quest_type:
            for key, value in type_data.items():
                setattr(quest_type, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Тип `{type_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_quest_type(self, type_id: int):
        """Удаление типа квеста."""
        query = select(QuestTypes).where(QuestTypes.type_id == type_id)
        result = await self.db_session.execute(query)
        quest_type = result.scalar()

        if quest_type:
            await self.db_session.delete(quest_type)
            await self.db_session.commit()
            return {"status": "success", "message": f"Тип `{type_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


class QuestConditionsManager:
    """Менеджер для работы с `quest_conditions` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_condition(self, condition_id: int, condition_data: dict):
        """Добавление нового условия квеста."""
        condition = QuestConditions(condition_id=condition_id, **condition_data)
        self.db_session.add(condition)
        await self.db_session.commit()
        return {"status": "success", "message": f"Условие `{condition_data['condition_key']}` добавлено"}

    async def get_condition(self, condition_id: int):
        """Получение условия квеста по ID."""
        query = select(QuestConditions).where(QuestConditions.condition_id == condition_id)
        result = await self.db_session.execute(query)
        condition = result.scalar()
        return {"status": "found", "data": condition.__dict__} if condition else {"status": "error", "message": "Условие не найдено"}

    async def update_condition(self, condition_id: int, condition_data: dict):
        """Обновление условия квеста."""
        query = select(QuestConditions).where(QuestConditions.condition_id == condition_id)
        result = await self.db_session.execute(query)
        condition = result.scalar()

        if condition:
            for key, value in condition_data.items():
                setattr(condition, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Условие `{condition_id}` обновлено"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_condition(self, condition_id: int):
        """Удаление условия квеста."""
        query = select(QuestConditions).where(QuestConditions.condition_id == condition_id)
        result = await self.db_session.execute(query)
        condition = result.scalar()

        if condition:
            await self.db_session.delete(condition)
            await self.db_session.commit()
            return {"status": "success", "message": f"Условие `{condition_id}` удалено"}
        return {"status": "error", "message": "Запись не найдена"}


class QuestRequirementsManager:
    """Менеджер для работы с `quest_requirements` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_requirement(self, requirement_id: int, requirement_data: dict):
        """Добавление нового требования квеста."""
        requirement = QuestRequirements(requirement_id=requirement_id, **requirement_data)
        self.db_session.add(requirement)
        await self.db_session.commit()
        return {"status": "success", "message": f"Требование `{requirement_data['requirement_key']}` добавлено"}

    async def get_requirement(self, requirement_id: int):
        """Получение требования квеста по ID."""
        query = select(QuestRequirements).where(QuestRequirements.requirement_id == requirement_id)
        result = await self.db_session.execute(query)
        requirement = result.scalar()
        return {"status": "found", "data": requirement.__dict__} if requirement else {"status": "error", "message": "Требование не найдено"}

    async def update_requirement(self, requirement_id: int, requirement_data: dict):
        """Обновление требования квеста."""
        query = select(QuestRequirements).where(QuestRequirements.requirement_id == requirement_id)
        result = await self.db_session.execute(query)
        requirement = result.scalar()

        if requirement:
            for key, value in requirement_data.items():
                setattr(requirement, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Требование `{requirement_id}` обновлено"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_requirement(self, requirement_id: int):
        """Удаление требования квеста."""
        query = select(QuestRequirements).where(QuestRequirements.requirement_id == requirement_id)
        result = await self.db_session.execute(query)
        requirement = result.scalar()

        if requirement:
            await self.db_session.delete(requirement)
            await self.db_session.commit()
            return {"status": "success", "message": f"Требование `{requirement_id}` удалено"}
        return {"status": "error", "message": "Запись не найдена"}


class QuestRewardsManager:
    """Менеджер для работы с `quest_rewards` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_reward(self, reward_id: int, reward_data: dict):
        """Добавление новой награды."""
        reward = QuestRewards(id=reward_id, **reward_data)
        self.db_session.add(reward)
        await self.db_session.commit()
        return {"status": "success", "message": f"Награда `{reward_data['reward_name']}` добавлена"}

    async def get_reward(self, reward_id: int):
        """Получение награды по ID."""
        query = select(QuestRewards).where(QuestRewards.id == reward_id)
        result = await self.db_session.execute(query)
        reward = result.scalar()
        return {"status": "found", "data": reward.__dict__} if reward else {"status": "error", "message": "Награда не найдена"}

    async def update_reward(self, reward_id: int, reward_data: dict):
        """Обновление награды."""
        query = select(QuestRewards).where(QuestRewards.id == reward_id)
        result = await self.db_session.execute(query)
        reward = result.scalar()

        if reward:
            for key, value in reward_data.items():
                setattr(reward, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Награда `{reward_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_reward(self, reward_id: int):
        """Удаление награды."""
        query = select(QuestRewards).where(QuestRewards.id == reward_id)
        result = await self.db_session.execute(query)
        reward = result.scalar()

        if reward:
            await self.db_session.delete(reward)
            await self.db_session.commit()
            return {"status": "success", "message": f"Награда `{reward_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}
