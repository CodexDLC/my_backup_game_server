from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

# Импортируем нашу финальную модель
from game_server.database.models.models import InventoryRuleGenerator

class InventoryRuleGeneratorManager:
    """
    Менеджер для выполнения CRUDS-операций с шаблонами генерации.
    Полностью асинхронная версия, соответствующая финальной модели.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_rule_key(self, rule_key: str) -> Optional[InventoryRuleGenerator]:
        """
        Находит правило по его первичному ключу (текстовому).
        """
        # .get() - самый эффективный способ получения объекта по PK
        return await self.session.get(InventoryRuleGenerator, rule_key)

    async def get_by_rule_id(self, rule_id: int) -> Optional[InventoryRuleGenerator]:
        """Находит правило по его уникальному числовому ID."""
        query = select(InventoryRuleGenerator).filter(InventoryRuleGenerator.rule_id == rule_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[InventoryRuleGenerator]:
        """Асинхронно возвращает все существующие правила."""
        query = select(InventoryRuleGenerator)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_matching_rules(self, quality_level: int, conditions: Dict[str, Any]) -> List[InventoryRuleGenerator]:
        """Асинхронно находит все подходящие шаблоны."""
        query = select(InventoryRuleGenerator).filter(InventoryRuleGenerator.quality_level == quality_level)
        if conditions:
            query = query.filter(InventoryRuleGenerator.activation_conditions.contains(conditions))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def upsert_rule(self, rule_data: Dict[str, Any]) -> InventoryRuleGenerator:
        """
        Обновляет правило, если оно существует (по полю 'rule_key'), или создает новое.
        Асинхронная версия "найти-и-обновить-или-создать".
        """
        rule_key = rule_data.get("rule_key")
        if not rule_key:
            raise ValueError("Поле 'rule_key' обязательно для операции upsert.")

        db_rule = await self.get_by_rule_key(rule_key)

        if db_rule:
            # UPDATE
            for key, value in rule_data.items():
                setattr(db_rule, key, value)
        else:
            # INSERT
            db_rule = InventoryRuleGenerator(**rule_data)
            self.session.add(db_rule)

        await self.session.commit()
        await self.session.refresh(db_rule)
        return db_rule

    async def delete_by_rule_key(self, rule_key: str) -> bool:
        """Удаляет правило по его первичному ключу (текстовому)."""
        db_rule = await self.get_by_rule_key(rule_key)
        if db_rule:
            await self.session.delete(db_rule)
            await self.session.commit()
            return True
        return False