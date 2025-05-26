from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_accessory_templates(action: str, accessory_id: int = None, accessory_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `accessory_templates`."""
    
    if action == "insert" and accessory_data:
        query = text("""
            INSERT INTO accessory_templates (id, base_item_code, suffix_code, name, rarity, color, energy_pool_bonus,
                                             regen_energy_rate, magic_defense_bonus, absorption_bonus, reflect_damage,
                                             damage_boost, durability, excluded_bonus_type, effect_description,
                                             is_fragile, strength_percentage)
            VALUES (:id, :base_item_code, :suffix_code, :name, :rarity, :color, :energy_pool_bonus, 
                    :regen_energy_rate, :magic_defense_bonus, :absorption_bonus, :reflect_damage, 
                    :damage_boost, :durability, :excluded_bonus_type, :effect_description, 
                    :is_fragile, :strength_percentage)
        """)
        await db_session.execute(query, {"id": accessory_id, **accessory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_data['name']}` добавлен"}

    elif action == "get" and accessory_id:
        query = text("SELECT * FROM accessory_templates WHERE id = :accessory_id")
        result = await db_session.execute(query, {"accessory_id": accessory_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Аксессуар не найден"}

    elif action == "update" and accessory_id and accessory_data:
        updates = ", ".join(f"{key} = :{key}" for key in accessory_data.keys())
        query = text(f"""
            UPDATE accessory_templates SET {updates}
            WHERE id = :accessory_id
        """)
        await db_session.execute(query, {"accessory_id": accessory_id, **accessory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_id}` обновлён"}

    elif action == "delete" and accessory_id:
        query = text("DELETE FROM accessory_templates WHERE id = :accessory_id")
        await db_session.execute(query, {"accessory_id": accessory_id})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_accessory_templates(action: str, accessory_id: int = None, accessory_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `accessory_templates`."""
    
    if action == "insert" and accessory_data:
        query = text("""
            INSERT INTO accessory_templates (id, base_item_code, suffix_code, name, rarity, color, energy_pool_bonus,
                                             regen_energy_rate, magic_defense_bonus, absorption_bonus, reflect_damage,
                                             damage_boost, durability, excluded_bonus_type, effect_description,
                                             is_fragile, strength_percentage)
            VALUES (:id, :base_item_code, :suffix_code, :name, :rarity, :color, :energy_pool_bonus, 
                    :regen_energy_rate, :magic_defense_bonus, :absorption_bonus, :reflect_damage, 
                    :damage_boost, :durability, :excluded_bonus_type, :effect_description, 
                    :is_fragile, :strength_percentage)
        """)
        await db_session.execute(query, {"id": accessory_id, **accessory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_data['name']}` добавлен"}

    elif action == "get" and accessory_id:
        query = text("SELECT * FROM accessory_templates WHERE id = :accessory_id")
        result = await db_session.execute(query, {"accessory_id": accessory_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Аксессуар не найден"}

    elif action == "update" and accessory_id and accessory_data:
        updates = ", ".join(f"{key} = :{key}" for key in accessory_data.keys())
        query = text(f"""
            UPDATE accessory_templates SET {updates}
            WHERE id = :accessory_id
        """)
        await db_session.execute(query, {"accessory_id": accessory_id, **accessory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_id}` обновлён"}

    elif action == "delete" and accessory_id:
        query = text("DELETE FROM accessory_templates WHERE id = :accessory_id")
        await db_session.execute(query, {"accessory_id": accessory_id})
        await db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_weapon_templates(action: str, weapon_id: int = None, weapon_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `weapon_templates`."""
    
    if action == "insert" and weapon_data:
        query = text("""
            INSERT INTO weapon_templates (id, base_item_code, suffix_code, name, rarity, color, p_atk, m_atk,
                                          crit_chance, crit_damage_bonus, armor_penetration, durability, accuracy,
                                          hp_steal_percent, effect_description, allowed_for_class, visual_asset,
                                          is_fragile, strength_percentage)
            VALUES (:id, :base_item_code, :suffix_code, :name, :rarity, :color, :p_atk, :m_atk, :crit_chance, 
                    :crit_damage_bonus, :armor_penetration, :durability, :accuracy, :hp_steal_percent, 
                    :effect_description, :allowed_for_class, :visual_asset, :is_fragile, :strength_percentage)
        """)
        await db_session.execute(query, {"id": weapon_id, **weapon_data})
        await db_session.commit()
        return {"status": "success", "message": f"Оружие `{weapon_data['name']}` добавлено"}

    elif action == "get" and weapon_id:
        query = text("SELECT * FROM weapon_templates WHERE id = :weapon_id")
        result = await db_session.execute(query, {"weapon_id": weapon_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Оружие не найдено"}

    elif action == "update" and weapon_id and weapon_data:
        updates = ", ".join(f"{key} = :{key}" for key in weapon_data.keys())
        query = text(f"""
            UPDATE weapon_templates SET {updates}
            WHERE id = :weapon_id
        """)
        await db_session.execute(query, {"weapon_id": weapon_id, **weapon_data})
        await db_session.commit()
        return {"status": "success", "message": f"Оружие `{weapon_id}` обновлено"}

    elif action == "delete" and weapon_id:
        query = text("DELETE FROM weapon_templates WHERE id = :weapon_id")
        await db_session.execute(query, {"weapon_id": weapon_id})
        await db_session.commit()
        return {"status": "success", "message": f"Оружие `{weapon_id}` удалено"}

    return {"status": "error", "message": "Неверные параметры"}


