# game_server/Logic/InfrastructureLogic/DataAccessLogic/manager/generators/ORM_equipment_template_repository.py

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Убедитесь, что этот импорт соответствует вашей модели EquipmentTemplate
from game_server.database.models.models import EquipmentTemplate


class EquipmentTemplateRepository: # Переименовано, чтобы отразить async и репозиторий
    """
    Репозиторий для выполнения асинхронных CRUD-операций над сущностью EquipmentTemplate.
    Отвечает за взаимодействие с базой данных на уровне DataAccess, используя AsyncSession.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает новую запись EquipmentTemplate в базе данных.
        """
        new_template = EquipmentTemplate(**data)
        self.session.add(new_template)
        await self.session.flush()
        await self.session.refresh(new_template)
        return new_template

    async def upsert(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает или обновляет запись EquipmentTemplate, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Предполагается, что 'item_code' является уникальным ключом для конфликта.
        """
        insert_stmt = pg_insert(EquipmentTemplate).values(**data)

        # Поля для обновления. Эти поля должны соответствовать вашей модели EquipmentTemplate
        update_fields = {
            "display_name": insert_stmt.excluded.display_name,
            "category": insert_stmt.excluded.category,
            "sub_category": insert_stmt.excluded.sub_category,
            "equip_slot": insert_stmt.excluded.equip_slot,
            "inventory_size": insert_stmt.excluded.inventory_size,
            "material_code": insert_stmt.excluded.material_code,
            "suffix_code": insert_stmt.excluded.suffix_code,
            "rarity_level": insert_stmt.excluded.rarity_level,
            "specific_name": insert_stmt.excluded.specific_name,
            "base_modifiers_json": insert_stmt.excluded.base_modifiers_json,
            # Добавьте сюда любые другие поля, которые должны обновляться при конфликте
        }

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EquipmentTemplate.item_code], # Конфликт по item_code (уникальный ключ)
            set_=update_fields
        ).returning(EquipmentTemplate)

        result = await self.session.execute(on_conflict_stmt)
        updated_or_inserted_item = result.scalar_one()
        await self.session.flush()
        await self.session.refresh(updated_or_inserted_item)
        return updated_or_inserted_item

    async def upsert_many(self, items_data: List[Dict[str, Any]]) -> int:
        """
        Массовая вставка или обновление (UPSERT) списка шаблонов предметов.
        """
        if not items_data:
            return 0

        insert_stmt = pg_insert(EquipmentTemplate).values(items_data)

        # Получаем все колонки модели, кроме тех, что являются первичными ключами
        # или по которым происходит конфликт (item_code)
        pk_names = [col.name for col in EquipmentTemplate.__table__.primary_key.columns]
        
        update_fields = {
            col.name: getattr(insert_stmt.excluded, col.name)
            for col in EquipmentTemplate.__table__.columns
            if col.name not in pk_names and col.name != 'item_code'
        }

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EquipmentTemplate.item_code], # Конфликт по item_code
            set_=update_fields
        )
        
        result = await self.session.execute(on_conflict_stmt)
        # Поскольку execute() не возвращает количество строк для UPSERT в async-режиме напрямую,
        # это число будет примерным или потребует дополнительного запроса.
        # Для простоты пока вернем 0 или адаптируйте под вашу ORM-стратегию подсчета.
        # В реальной системе можно сделать returning(func.count(EquipmentTemplate.item_id))
        # или просто рассчитывать, что все в батче были успешно обработаны.
        return len(items_data) # Возвращаем количество переданных элементов как "обработано"


    async def get_by_item_code(self, item_code: str) -> Optional[EquipmentTemplate]:
        """
        Получает запись EquipmentTemplate по её item_code.
        """
        stmt = select(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_item_codes(self) -> List[str]:
        """
        Получает список всех существующих item_code из базы данных.
        Используется планировщиком для определения недостающих шаблонов.
        """
        stmt = select(EquipmentTemplate.item_code)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_templates(self) -> List[EquipmentTemplate]:
        """
        Получает все записи из таблицы EquipmentTemplate.
        """
        stmt = select(EquipmentTemplate).order_by(EquipmentTemplate.item_code)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, item_code: str, update_data: Dict[str, Any]) -> Optional[EquipmentTemplate]:
        """
        Обновляет запись EquipmentTemplate по её item_code.
        """
        if not update_data:
            return await self.get_by_item_code(item_code)

        stmt = (
            update(EquipmentTemplate)
            .where(EquipmentTemplate.item_code == item_code)
            .values(**update_data)
            .returning(EquipmentTemplate)
        )
        result = await self.session.execute(stmt)
        updated_template = result.scalar_one_or_none()
        if updated_template:
            await self.session.flush()
            await self.session.refresh(updated_template)
        return updated_template

    async def delete_by_item_code(self, item_code: str) -> bool:
        """
        Удаляет запись EquipmentTemplate по её item_code.
        """
        stmt = delete(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
        result = await self.session.execute(stmt)
        return result.rowcount > 0