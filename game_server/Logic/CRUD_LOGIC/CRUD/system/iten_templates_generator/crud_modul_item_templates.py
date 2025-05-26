from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_suffixes(action: str, suffix_code: int = None, suffix_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `suffixes`."""
    
    if action == "insert" and suffix_data:
        query = text("""
            INSERT INTO suffixes (suffix_code, fragment, is_for_weapon, is_for_armor, is_for_accessory, 
                                  mod1_code, mod1_value, mod2_code, mod2_value, mod3_code, mod3_value, 
                                  mod4_code, mod4_value)
            VALUES (:suffix_code, :fragment, :is_for_weapon, :is_for_armor, :is_for_accessory, 
                    :mod1_code, :mod1_value, :mod2_code, :mod2_value, :mod3_code, :mod3_value, 
                    :mod4_code, :mod4_value)
        """)
        await db_session.execute(query, {"suffix_code": suffix_code, **suffix_data})
        await db_session.commit()
        return {"status": "success", "message": f"Суффикс `{suffix_data['fragment']}` добавлен"}

    elif action == "get" and suffix_code:
        query = text("SELECT * FROM suffixes WHERE suffix_code = :suffix_code")
        result = await db_session.execute(query, {"suffix_code": suffix_code})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Суффикс не найден"}

    elif action == "update" and suffix_code and suffix_data:
        updates = ", ".join(f"{key} = :{key}" for key in suffix_data.keys())
        query = text(f"""
            UPDATE suffixes SET {updates}
            WHERE suffix_code = :suffix_code
        """)
        await db_session.execute(query, {"suffix_code": suffix_code, **suffix_data})
        await db_session.commit()
        return {"status": "success", "message": f"Суффикс `{suffix_code}` обновлён"}

    elif action == "delete" and suffix_code:
        query = text("DELETE FROM suffixes WHERE suffix_code = :suffix_code")
        await db_session.execute(query, {"suffix_code": suffix_code})
        await db_session.commit()
        return {"status": "success", "message": f"Суффикс `{suffix_code}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_modifiers_library(action: str, modifier_id: int = None, modifier_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `modifiers_library`."""
    
    if action == "insert" and modifier_data:
        query = text("""
            INSERT INTO modifiers_library (id, access_modifier, modifier_name, effect_description)
            VALUES (:id, :access_modifier, :modifier_name, :effect_description)
        """)
        await db_session.execute(query, {"id": modifier_id, **modifier_data})
        await db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_data['modifier_name']}` добавлен"}

    elif action == "get" and modifier_id:
        query = text("SELECT * FROM modifiers_library WHERE id = :modifier_id")
        result = await db_session.execute(query, {"modifier_id": modifier_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Модификатор не найден"}

    elif action == "update" and modifier_id and modifier_data:
        updates = ", ".join(f"{key} = :{key}" for key in modifier_data.keys())
        query = text(f"""
            UPDATE modifiers_library SET {updates}
            WHERE id = :modifier_id
        """)
        await db_session.execute(query, {"modifier_id": modifier_id, **modifier_data})
        await db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_id}` обновлён"}

    elif action == "delete" and modifier_id:
        query = text("DELETE FROM modifiers_library WHERE id = :modifier_id")
        await db_session.execute(query, {"modifier_id": modifier_id})
        await db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_template_modifier_defaults(action: str, base_item_code: int = None, modifier_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `template_modifier_defaults`."""
    
    if action == "insert" and modifier_data:
        query = text("""
            INSERT INTO template_modifier_defaults (base_item_code, access_modifier, default_value)
            VALUES (:base_item_code, :access_modifier, :default_value)
        """)
        await db_session.execute(query, {"base_item_code": base_item_code, **modifier_data})
        await db_session.commit()
        return {"status": "success", "message": f"Модификатор `{modifier_data['access_modifier']}` добавлен для `{base_item_code}`"}

    elif action == "get" and base_item_code:
        query = text("SELECT * FROM template_modifier_defaults WHERE base_item_code = :base_item_code")
        result = await db_session.execute(query, {"base_item_code": base_item_code})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Модификаторы не найдены"}

    elif action == "update" and base_item_code and modifier_data:
        updates = ", ".join(f"{key} = :{key}" for key in modifier_data.keys())
        query = text(f"""
            UPDATE template_modifier_defaults SET {updates}
            WHERE base_item_code = :base_item_code
        """)
        await db_session.execute(query, {"base_item_code": base_item_code, **modifier_data})
        await db_session.commit()
        return {"status": "success", "message": f"Модификаторы `{base_item_code}` обновлены"}

    elif action == "delete" and base_item_code:
        query = text("DELETE FROM template_modifier_defaults WHERE base_item_code = :base_item_code")
        await db_session.execute(query, {"base_item_code": base_item_code})
        await db_session.commit()
        return {"status": "success", "message": f"Модификаторы `{base_item_code}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_item_base(action: str, base_item_code: int = None, item_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `item_base`."""
    
    if action == "insert" and item_data:
        query = text("""
            INSERT INTO item_base (base_item_code, item_name, category, equip_slot, base_durability, base_weight)
            VALUES (:base_item_code, :item_name, :category, :equip_slot, :base_durability, :base_weight)
        """)
        await db_session.execute(query, {"base_item_code": base_item_code, **item_data})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{item_data['item_name']}` добавлен"}

    elif action == "get" and base_item_code:
        query = text("SELECT * FROM item_base WHERE base_item_code = :base_item_code")
        result = await db_session.execute(query, {"base_item_code": base_item_code})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Предмет не найден"}

    elif action == "update" and base_item_code and item_data:
        updates = ", ".join(f"{key} = :{key}" for key in item_data.keys())
        query = text(f"""
            UPDATE item_base SET {updates}
            WHERE base_item_code = :base_item_code
        """)
        await db_session.execute(query, {"base_item_code": base_item_code, **item_data})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{base_item_code}` обновлен"}

    elif action == "delete" and base_item_code:
        query = text("DELETE FROM item_base WHERE base_item_code = :base_item_code")
        await db_session.execute(query, {"base_item_code": base_item_code})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{base_item_code}` удален"}

    return {"status": "error", "message": "Неверные параметры"}
