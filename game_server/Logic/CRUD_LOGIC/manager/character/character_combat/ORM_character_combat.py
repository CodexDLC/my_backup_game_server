# game_server\Logic\ORM_LOGIC\ORM\player\orm_player_magic_attack.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select

from game_server.database.models.models import CharacterStatus, PlayerMagicAttack, PlayerMagicDefense, PlayerPhysicalAttack, PlayerPhysicalDefense




class PlayerMagicAttackManager:
    """Менеджер для работы с `player_magic_attack` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_magic_attack(self, player_id: int, magic_data: dict):
        """Добавление новой записи о магической атаке."""
        attack = PlayerMagicAttack(player_id=player_id, **magic_data)
        self.db_session.add(attack)
        await self.db_session.commit()
        return {"status": "success", "message": f"Магическая атака `{player_id}` добавлена"}

    async def get_magic_attack(self, player_id: int):
        """Получение данных по магической атаке игрока."""
        query = select(PlayerMagicAttack).where(PlayerMagicAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Данные не найдены"}

    async def update_magic_attack(self, player_id: int, magic_data: dict):
        """Обновление данных о магической атаке."""
        query = select(PlayerMagicAttack).where(PlayerMagicAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        attack = result.scalar()

        if attack:
            for key, value in magic_data.items():
                setattr(attack, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Магическая атака `{player_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_magic_attack(self, player_id: int):
        """Удаление записи о магической атаке игрока."""
        query = select(PlayerMagicAttack).where(PlayerMagicAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        attack = result.scalar()

        if attack:
            await self.db_session.delete(attack)
            await self.db_session.commit()
            return {"status": "success", "message": f"Данные `{player_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}



class PlayerMagicDefenseManager:
    """Менеджер для работы с `player_magic_defense` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_magic_defense(self, player_id: int, defense_data: dict):
        """Добавление новой записи о магической защите."""
        defense = PlayerMagicDefense(player_id=player_id, **defense_data)
        self.db_session.add(defense)
        await self.db_session.commit()
        return {"status": "success", "message": f"Магическая защита `{player_id}` добавлена"}

    async def get_magic_defense(self, player_id: int):
        """Получение данных по магической защите игрока."""
        query = select(PlayerMagicDefense).where(PlayerMagicDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Данные не найдены"}

    async def update_magic_defense(self, player_id: int, defense_data: dict):
        """Обновление данных о магической защите."""
        query = select(PlayerMagicDefense).where(PlayerMagicDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        defense = result.scalar()

        if defense:
            for key, value in defense_data.items():
                setattr(defense, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Магическая защита `{player_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_magic_defense(self, player_id: int):
        """Удаление записи о магической защите игрока."""
        query = select(PlayerMagicDefense).where(PlayerMagicDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        defense = result.scalar()

        if defense:
            await self.db_session.delete(defense)
            await self.db_session.commit()
            return {"status": "success", "message": f"Данные `{player_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}

class PlayerPhysicalAttackManager:
    """Менеджер для работы с `player_physical_attack` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_physical_attack(self, player_id: int, attack_data: dict):
        """Добавление новой записи о физической атаке."""
        attack = PlayerPhysicalAttack(player_id=player_id, **attack_data)
        self.db_session.add(attack)
        await self.db_session.commit()
        return {"status": "success", "message": f"Атака `{player_id}` добавлена"}

    async def get_physical_attack(self, player_id: int):
        """Получение данных по физической атаке игрока."""
        query = select(PlayerPhysicalAttack).where(PlayerPhysicalAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Данные не найдены"}

    async def update_physical_attack(self, player_id: int, attack_data: dict):
        """Обновление данных о физической атаке."""
        query = select(PlayerPhysicalAttack).where(PlayerPhysicalAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        attack = result.scalar()

        if attack:
            for key, value in attack_data.items():
                setattr(attack, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Атака `{player_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_physical_attack(self, player_id: int):
        """Удаление записи о физической атаке игрока."""
        query = select(PlayerPhysicalAttack).where(PlayerPhysicalAttack.player_id == player_id)
        result = await self.db_session.execute(query)
        attack = result.scalar()

        if attack:
            await self.db_session.delete(attack)
            await self.db_session.commit()
            return {"status": "success", "message": f"Данные `{player_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}



class PlayerPhysicalDefenseManager:
    """Менеджер для работы с `player_physical_defense` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_physical_defense(self, player_id: int, defense_data: dict):
        """Добавление новой записи о физической защите."""
        defense = PlayerPhysicalDefense(player_id=player_id, **defense_data)
        self.db_session.add(defense)
        await self.db_session.commit()
        return {"status": "success", "message": f"Физическая защита `{player_id}` добавлена"}

    async def get_physical_defense(self, player_id: int):
        """Получение данных по физической защите игрока."""
        query = select(PlayerPhysicalDefense).where(PlayerPhysicalDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Данные не найдены"}

    async def update_physical_defense(self, player_id: int, defense_data: dict):
        """Обновление данных о физической защите."""
        query = select(PlayerPhysicalDefense).where(PlayerPhysicalDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        defense = result.scalar()

        if defense:
            for key, value in defense_data.items():
                setattr(defense, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Физическая защита `{player_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_physical_defense(self, player_id: int):
        """Удаление записи о физической защите игрока."""
        query = select(PlayerPhysicalDefense).where(PlayerPhysicalDefense.player_id == player_id)
        result = await self.db_session.execute(query)
        defense = result.scalar()

        if defense:
            await self.db_session.delete(defense)
            await self.db_session.commit()
            return {"status": "success", "message": f"Данные `{player_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}


class CharacterStatusManager:
    """Менеджер для работы с `character_status` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_status(self, player_id: int, status_data: dict):
        """Добавление новой записи о статусе персонажа."""
        status = CharacterStatus(player_id=player_id, **status_data)
        self.db_session.add(status)
        await self.db_session.commit()
        return {"status": "success", "message": f"Статус `{player_id}` добавлен"}

    async def get_status(self, player_id: int):
        """Получение данных по статусу персонажа."""
        query = select(CharacterStatus).where(CharacterStatus.player_id == player_id)
        result = await self.db_session.execute(query)
        row = result.scalar()
        return {"status": "found", "data": row.__dict__} if row else {"status": "error", "message": "Статус не найден"}

    async def update_status(self, player_id: int, status_data: dict):
        """Обновление данных о статусе персонажа."""
        query = select(CharacterStatus).where(CharacterStatus.player_id == player_id)
        result = await self.db_session.execute(query)
        status = result.scalar()

        if status:
            for key, value in status_data.items():
                setattr(status, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Статус `{player_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_status(self, player_id: int):
        """Удаление записи о статусе персонажа."""
        query = select(CharacterStatus).where(CharacterStatus.player_id == player_id)
        result = await self.db_session.execute(query)
        status = result.scalar()

        if status:
            await self.db_session.delete(status)
            await self.db_session.commit()
            return {"status": "success", "message": f"Статус `{player_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
