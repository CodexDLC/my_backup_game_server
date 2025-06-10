

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import QuestFlags, QuestRewards, QuestSteps



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



class QuestStepsManager:
    """Менеджер для работы с `quest_steps` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_step(self, step_key: str, step_data: dict):
        """Добавление нового шага квеста."""
        step = QuestSteps(step_key=step_key, **step_data)
        self.db_session.add(step)
        await self.db_session.commit()
        return {"status": "success", "message": f"Шаг `{step_key}` добавлен"}

    async def get_step(self, step_key: str):
        """Получение шага квеста по ключу."""
        query = select(QuestSteps).where(QuestSteps.step_key == step_key)
        result = await self.db_session.execute(query)
        step = result.scalar()
        return {"status": "found", "data": step.__dict__} if step else {"status": "error", "message": "Шаг не найден"}

    async def update_step(self, step_key: str, step_data: dict):
        """Обновление шага квеста."""
        query = select(QuestSteps).where(QuestSteps.step_key == step_key)
        result = await self.db_session.execute(query)
        step = result.scalar()

        if step:
            for key, value in step_data.items():
                setattr(step, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Шаг `{step_key}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_step(self, step_key: str):
        """Удаление шага квеста."""
        query = select(QuestSteps).where(QuestSteps.step_key == step_key)
        result = await self.db_session.execute(query)
        step = result.scalar()

        if step:
            await self.db_session.delete(step)
            await self.db_session.commit()
            return {"status": "success", "message": f"Шаг `{step_key}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}




class QuestFlagsManager:
    """Менеджер для работы с `quest_flags` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_flag(self, flag_id: int, flag_data: dict):
        """Добавление нового флага квеста."""
        flag = QuestFlags(flag_id=flag_id, **flag_data)
        self.db_session.add(flag)
        await self.db_session.commit()
        return {"status": "success", "message": f"Флаг `{flag_data['flag_key']}` добавлен"}

    async def get_flag(self, flag_id: int):
        """Получение флага квеста по ID."""
        query = select(QuestFlags).where(QuestFlags.flag_id == flag_id)
        result = await self.db_session.execute(query)
        flag = result.scalar()
        return {"status": "found", "data": flag.__dict__} if flag else {"status": "error", "message": "Флаг не найден"}

    async def update_flag(self, flag_id: int, flag_data: dict):
        """Обновление флага квеста."""
        query = select(QuestFlags).where(QuestFlags.flag_id == flag_id)
        result = await self.db_session.execute(query)
        flag = result.scalar()

        if flag:
            for key, value in flag_data.items():
                setattr(flag, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Флаг `{flag_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_flag(self, flag_id: int):
        """Удаление флага квеста."""
        query = select(QuestFlags).where(QuestFlags.flag_id == flag_id)
        result = await self.db_session.execute(query)
        flag = result.scalar()

        if flag:
            await self.db_session.delete(flag)
            await self.db_session.commit()
            return {"status": "success", "message": f"Флаг `{flag_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


