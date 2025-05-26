# game_server\Logic\ORM_LOGIC\managers\orm_discord_bindings.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import AppliedPermissions, DiscordBindings, DiscordQuestDescriptions, StateEntitiesDiscord

class DiscordBindingsManager:
    """Менеджер для работы с `discord_bindings` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_binding(self, guild_id: int, binding_data: dict):
        """Добавление новой связи."""
        binding = DiscordBindings(guild_id=guild_id, **binding_data)
        self.db_session.add(binding)
        await self.db_session.commit()
        return {"status": "success", "message": f"Связь `{guild_id}` добавлена"}

    async def get_binding(self, guild_id: int):
        """Получение связи по guild_id."""
        query = select(DiscordBindings).where(DiscordBindings.guild_id == guild_id)
        result = await self.db_session.execute(query)
        binding = result.scalar()
        return {"status": "found", "data": binding.__dict__} if binding else {"status": "error", "message": "Связь не найдена"}

    async def update_binding(self, guild_id: int, binding_data: dict):
        """Обновление связи."""
        query = select(DiscordBindings).where(DiscordBindings.guild_id == guild_id)
        result = await self.db_session.execute(query)
        binding = result.scalar()

        if binding:
            for key, value in binding_data.items():
                setattr(binding, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Связь `{guild_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_binding(self, guild_id: int):
        """Удаление связи."""
        query = select(DiscordBindings).where(DiscordBindings.guild_id == guild_id)
        result = await self.db_session.execute(query)
        binding = result.scalar()

        if binding:
            await self.db_session.delete(binding)
            await self.db_session.commit()
            return {"status": "success", "message": f"Связь `{guild_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}



class AppliedPermissionsManager:
    """Менеджер для работы с `applied_permissions` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_permission(self, guild_id: int, permission_data: dict):
        """Добавление новых прав доступа."""
        permission = AppliedPermissions(guild_id=guild_id, **permission_data)
        self.db_session.add(permission)
        await self.db_session.commit()
        return {"status": "success", "message": f"Права `{guild_id}` добавлены"}

    async def get_permissions(self, guild_id: int):
        """Получение списка прав по guild_id."""
        query = select(AppliedPermissions).where(AppliedPermissions.guild_id == guild_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Права не найдены"}

    async def update_permission(self, guild_id: int, permission_data: dict):
        """Обновление прав доступа."""
        query = select(AppliedPermissions).where(AppliedPermissions.guild_id == guild_id)
        result = await self.db_session.execute(query)
        permission = result.scalar()

        if permission:
            for key, value in permission_data.items():
                setattr(permission, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Права `{guild_id}` обновлены"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_permission(self, guild_id: int):
        """Удаление прав доступа."""
        query = select(AppliedPermissions).where(AppliedPermissions.guild_id == guild_id)
        result = await self.db_session.execute(query)
        permission = result.scalar()

        if permission:
            await self.db_session.delete(permission)
            await self.db_session.commit()
            return {"status": "success", "message": f"Права `{guild_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}

class StateEntitiesDiscordManager:
    """Менеджер для работы с `state_entities_discord` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_entity(self, guild_id: int, entity_data: dict):
        """Добавление новой записи в таблицу `state_entities_discord`."""
        entity = StateEntitiesDiscord(guild_id=guild_id, **entity_data)
        self.db_session.add(entity)
        await self.db_session.commit()
        return {"status": "success", "message": f"Роль `{entity_data['role_name']}` добавлена для гильдии `{guild_id}`"}

    async def get_entities(self, guild_id: int):
        """Получение записей по guild_id."""
        query = select(StateEntitiesDiscord).where(StateEntitiesDiscord.guild_id == guild_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Данные не найдены"}

    async def update_entity(self, guild_id: int, entity_data: dict):
        """Обновление записи в таблице `state_entities_discord`."""
        query = select(StateEntitiesDiscord).where(StateEntitiesDiscord.guild_id == guild_id)
        result = await self.db_session.execute(query)
        entity = result.scalar()

        if entity:
            for key, value in entity_data.items():
                setattr(entity, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Роль `{entity_data['role_name']}` обновлена для `{guild_id}`"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_entity(self, guild_id: int):
        """Удаление записи из `state_entities_discord`."""
        query = select(StateEntitiesDiscord).where(StateEntitiesDiscord.guild_id == guild_id)
        result = await self.db_session.execute(query)
        entity = result.scalar()

        if entity:
            await self.db_session.delete(entity)
            await self.db_session.commit()
            return {"status": "success", "message": f"Роль `{guild_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}


class DiscordQuestDescriptionsManager:
    """Менеджер для работы с `discord_quest_descriptions` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_quest_description(self, description_key: str, quest_data: dict):
        """Добавление описания квеста."""
        quest = DiscordQuestDescriptions(description_key=description_key, **quest_data)
        self.db_session.add(quest)
        await self.db_session.commit()
        return {"status": "success", "message": f"Квест `{description_key}` добавлен"}

    async def get_quest_description(self, description_key: str):
        """Получение описания квеста."""
        query = select(DiscordQuestDescriptions).where(DiscordQuestDescriptions.description_key == description_key)
        result = await self.db_session.execute(query)
        quest = result.scalar()
        return {"status": "found", "data": quest.__dict__} if quest else {"status": "error", "message": "Квест не найден"}

    async def update_quest_description(self, description_key: str, quest_data: dict):
        """Обновление описания квеста."""
        query = select(DiscordQuestDescriptions).where(DiscordQuestDescriptions.description_key == description_key)
        result = await self.db_session.execute(query)
        quest = result.scalar()

        if quest:
            for key, value in quest_data.items():
                setattr(quest, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Квест `{description_key}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_quest_description(self, description_key: str):
        """Удаление описания квеста."""
        query = select(DiscordQuestDescriptions).where(DiscordQuestDescriptions.description_key == description_key)
        result = await self.db_session.execute(query)
        quest = result.scalar()

        if quest:
            await self.db_session.delete(quest)
            await self.db_session.commit()
            return {"status": "success", "message": f"Квест `{description_key}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}