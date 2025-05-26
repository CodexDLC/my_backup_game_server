# game_server\Logic\ORM_LOGIC\managers\orm_suffixes.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import ItemBase, Suffixes, TemplateModifierDefaults

class SuffixesManager:
    """Менеджер для работы с `suffixes` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_suffix(self, suffix_code: int, suffix_data: dict):
        """Добавление нового суффикса."""
        suffix = Suffixes(suffix_code=suffix_code, **suffix_data)
        self.db_session.add(suffix)
        await self.db_session.commit()
        return {"status": "success", "message": f"Суффикс `{suffix_data['fragment']}` добавлен"}

    async def get_suffix(self, suffix_code: int):
        """Получение суффикса по его коду."""
        query = select(Suffixes).where(Suffixes.suffix_code == suffix_code)
        result = await self.db_session.execute(query)
        suffix = result.scalar()
        return {"status": "found", "data": suffix.__dict__} if suffix else {"status": "error", "message": "Суффикс не найден"}

    async def update_suffix(self, suffix_code: int, suffix_data: dict):
        """Обновление данных суффикса."""
        query = select(Suffixes).where(Suffixes.suffix_code == suffix_code)
        result = await self.db_session.execute(query)
        suffix = result.scalar()

        if suffix:
            for key, value in suffix_data.items():
                setattr(suffix, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Суффикс `{suffix_code}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_suffix(self, suffix_code: int):
        """Удаление суффикса."""
        query = select(Suffixes).where(Suffixes.suffix_code == suffix_code)
        result = await self.db_session.execute(query)
        suffix = result.scalar()

        if suffix:
            await self.db_session.delete(suffix)
            await self.db_session.commit()
            return {"status": "success", "message": f"Суффикс `{suffix_code}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}



# game_server\Logic\ORM_LOGIC\managers\orm_modifiers_library.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import ModifiersLibrary

class ModifiersLibraryManager:
    """Менеджер для работы с `modifiers_library` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_modifier(self, modifier_id: int, modifier_data: dict):
        """Добавление нового модификатора."""
        modifier = ModifiersLibrary(id=modifier_id, **modifier_data)
        self.db_session.add(modifier)
        await self.db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_data['modifier_name']}` добавлен"}

    async def get_modifier(self, modifier_id: int):
        """Получение модификатора по ID."""
        query = select(ModifiersLibrary).where(ModifiersLibrary.id == modifier_id)
        result = await self.db_session.execute(query)
        modifier = result.scalar()
        return {"status": "found", "data": modifier.__dict__} if modifier else {"status": "error", "message": "Модификатор не найден"}

    async def update_modifier(self, modifier_id: int, modifier_data: dict):
        """Обновление данных модификатора."""
        query = select(ModifiersLibrary).where(ModifiersLibrary.id == modifier_id)
        result = await self.db_session.execute(query)
        modifier = result.scalar()

        if modifier:
            for key, value in modifier_data.items():
                setattr(modifier, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Модификатор `{modifier_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_modifier(self, modifier_id: int):
        """Удаление модификатора."""
        query = select(ModifiersLibrary).where(ModifiersLibrary.id == modifier_id)
        result = await self.db_session.execute(query)
        modifier = result.scalar()

        if modifier:
            await self.db_session.delete(modifier)
            await self.db_session.commit()
            return {"status": "success", "message": f"Модификатор `{modifier_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


class TemplateModifierDefaultsManager:
    """Менеджер для работы с `template_modifier_defaults` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_modifier(self, base_item_code: int, modifier_data: dict):
        """Добавление стандартного модификатора для базового предмета."""
        modifier = TemplateModifierDefaults(base_item_code=base_item_code, **modifier_data)
        self.db_session.add(modifier)
        await self.db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_data['access_modifier']}` добавлен для `{base_item_code}`"}

    async def get_modifiers(self, base_item_code: int):
        """Получение стандартных модификаторов базового предмета."""
        query = select(TemplateModifierDefaults).where(TemplateModifierDefaults.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Модификаторы не найдены"}

    async def update_modifier(self, base_item_code: int, modifier_data: dict):
        """Обновление стандартных модификаторов базового предмета."""
        query = select(TemplateModifierDefaults).where(TemplateModifierDefaults.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        modifier = result.scalar()

        if modifier:
            for key, value in modifier_data.items():
                setattr(modifier, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Модификаторы `{base_item_code}` обновлены"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_modifier(self, base_item_code: int):
        """Удаление стандартных модификаторов базового предмета."""
        query = select(TemplateModifierDefaults).where(TemplateModifierDefaults.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        modifiers = result.scalars().all()

        if modifiers:
            for modifier in modifiers:
                await self.db_session.delete(modifier)

            await self.db_session.commit()
            return {"status": "success", "message": f"Модификаторы `{base_item_code}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}


class ItemBaseManager:
    """Менеджер для работы с `item_base` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_item(self, base_item_code: int, item_data: dict):
        """Добавление нового базового предмета."""
        item = ItemBase(base_item_code=base_item_code, **item_data)
        self.db_session.add(item)
        await self.db_session.commit()
        return {"status": "success", "message": f"Предмет `{item_data['item_name']}` добавлен"}

    async def get_item(self, base_item_code: int):
        """Получение базового предмета по его коду."""
        query = select(ItemBase).where(ItemBase.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        item = result.scalar()
        return {"status": "found", "data": item.__dict__} if item else {"status": "error", "message": "Предмет не найден"}

    async def update_item(self, base_item_code: int, item_data: dict):
        """Обновление данных базового предмета."""
        query = select(ItemBase).where(ItemBase.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            for key, value in item_data.items():
                setattr(item, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Предмет `{base_item_code}` обновлен"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_item(self, base_item_code: int):
        """Удаление базового предмета."""
        query = select(ItemBase).where(ItemBase.base_item_code == base_item_code)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            await self.db_session.delete(item)
            await self.db_session.commit()
            return {"status": "success", "message": f"Предмет `{base_item_code}` удален"}
        return {"status": "error", "message": "Запись не найдена"}
