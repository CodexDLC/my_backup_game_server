
from sqlalchemy import text
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession


async def manage_player_magic_attack(action: str, player_id: int = None, magic_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `player_magic_attack`."""
    if action == "insert" and magic_data:
        query = text("""
            INSERT INTO player_magic_attack (player_id, elemental_power_bonus, fire_power_bonus, water_power_bonus, air_power_bonus, 
            earth_power_bonus, light_power_bonus, dark_power_bonus, gray_magic_power_bonus)
            VALUES (:player_id, :elemental_power_bonus, :fire_power_bonus, :water_power_bonus, :air_power_bonus, 
            :earth_power_bonus, :light_power_bonus, :dark_power_bonus, :gray_magic_power_bonus)
        """)
        await db_session.execute(query, {"player_id": player_id, **magic_data})
        await db_session.commit()
        return {"status": "success", "message": f"Магическая атака `{player_id}` добавлена"}

    elif action == "get" and player_id:
        query = text("SELECT * FROM player_magic_attack WHERE player_id = :player_id")
        result = await db_session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Данные не найдены"}

    elif action == "update" and player_id and magic_data:
        updates = ", ".join(f"{key} = :{key}" for key in magic_data.keys())
        query = text(f"""
            UPDATE player_magic_attack SET {updates} WHERE player_id = :player_id
        """)
        await db_session.execute(query, {"player_id": player_id, **magic_data})
        await db_session.commit()
        return {"status": "success", "message": f"Магическая атака `{player_id}` обновлена"}

    elif action == "delete" and player_id:
        query = text("DELETE FROM player_magic_attack WHERE player_id = :player_id")
        await db_session.execute(query, {"player_id": player_id})
        await db_session.commit()
        return {"status": "success", "message": f"Данные `{player_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_player_magic_defense(action: str, player_id: int = None, defense_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `player_magic_defense`."""
    if action == "insert" and defense_data:
        query = text("""
            INSERT INTO player_magic_defense (player_id, fire_resistance, water_resistance, air_resistance, earth_resistance, 
            light_resistance, dark_resistance, gray_magic_resistance, magic_resistance_percent)
            VALUES (:player_id, :fire_resistance, :water_resistance, :air_resistance, :earth_resistance, 
            :light_resistance, :dark_resistance, :gray_magic_resistance, :magic_resistance_percent)
        """)
        await db_session.execute(query, {"player_id": player_id, **defense_data})
        await db_session.commit()
        return {"status": "success", "message": f"Магическая защита `{player_id}` добавлена"}

    elif action == "get" and player_id:
        query = text("SELECT * FROM player_magic_defense WHERE player_id = :player_id")
        result = await db_session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Данные не найдены"}

    elif action == "update" and player_id and defense_data:
        updates = ", ".join(f"{key} = :{key}" for key in defense_data.keys())
        query = text(f"""
            UPDATE player_magic_defense SET {updates} WHERE player_id = :player_id
        """)
        await db_session.execute(query, {"player_id": player_id, **defense_data})
        await db_session.commit()
        return {"status": "success", "message": f"Магическая защита `{player_id}` обновлена"}

    elif action == "delete" and player_id:
        query = text("DELETE FROM player_magic_defense WHERE player_id = :player_id")
        await db_session.execute(query, {"player_id": player_id})
        await db_session.commit()
        return {"status": "success", "message": f"Данные `{player_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_player_physical_attack(action: str, player_id: int = None, attack_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `player_physical_attack`."""
    if action == "insert" and attack_data:
        query = text("""
            INSERT INTO player_physical_attack (player_id, piercing_damage_bonus, slashing_damage_bonus, 
            blunt_damage_bonus, cutting_damage_bonus)
            VALUES (:player_id, :piercing_damage_bonus, :slashing_damage_bonus, :blunt_damage_bonus, :cutting_damage_bonus)
        """)
        await db_session.execute(query, {"player_id": player_id, **attack_data})
        await db_session.commit()
        return {"status": "success", "message": f"Атака `{player_id}` добавлена"}

    elif action == "get" and player_id:
        query = text("SELECT * FROM player_physical_attack WHERE player_id = :player_id")
        result = await db_session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Данные не найдены"}

    elif action == "update" and player_id and attack_data:
        updates = ", ".join(f"{key} = :{key}" for key in attack_data.keys())
        query = text(f"""
            UPDATE player_physical_attack SET {updates} WHERE player_id = :player_id
        """)
        await db_session.execute(query, {"player_id": player_id, **attack_data})
        await db_session.commit()
        return {"status": "success", "message": f"Атака `{player_id}` обновлена"}

    elif action == "delete" and player_id:
        query = text("DELETE FROM player_physical_attack WHERE player_id = :player_id")
        await db_session.execute(query, {"player_id": player_id})
        await db_session.commit()
        return {"status": "success", "message": f"Данные `{player_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_player_physical_defense(action: str, player_id: int = None, defense_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `player_physical_defense`."""
    if action == "insert" and defense_data:
        query = text("""
            INSERT INTO player_physical_defense (player_id, piercing_resistance, slashing_resistance, 
            blunt_resistance, cutting_resistance, physical_resistance_percent)
            VALUES (:player_id, :piercing_resistance, :slashing_resistance, :blunt_resistance, :cutting_resistance, 
            :physical_resistance_percent)
        """)
        await db_session.execute(query, {"player_id": player_id, **defense_data})
        await db_session.commit()
        return {"status": "success", "message": f"Физическая защита `{player_id}` добавлена"}

    elif action == "get" and player_id:
        query = text("SELECT * FROM player_physical_defense WHERE player_id = :player_id")
        result = await db_session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Данные не найдены"}

    elif action == "update" and player_id and defense_data:
        updates = ", ".join(f"{key} = :{key}" for key in defense_data.keys())
        query = text(f"""
            UPDATE player_physical_defense SET {updates} WHERE player_id = :player_id
        """)
        await db_session.execute(query, {"player_id": player_id, **defense_data})
        await db_session.commit()
        return {"status": "success", "message": f"Физическая защита `{player_id}` обновлена"}

    elif action == "delete" and player_id:
        query = text("DELETE FROM player_physical_defense WHERE player_id = :player_id")
        await db_session.execute(query, {"player_id": player_id})
        await db_session.commit()
        return {"status": "success", "message": f"Данные `{player_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_character_status(action: str, player_id: int = None, status_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `character_status`."""
    if action == "insert" and status_data:
        query = text("""
            INSERT INTO character_status (player_id, current_health, max_health, current_energy, crit_chance, 
            crit_damage_bonus, anti_crit_chance, anti_crit_damage, dodge_chance, anti_dodge_chance, counter_attack_chance, 
            parry_chance, block_chance, armor_penetration, physical_attack, magical_attack, magic_resistance, 
            physical_resistance, mana_cost_reduction, regen_health_rate, energy_regeneration_bonus, energy_pool_bonus, 
            absorption_bonus, shield_value, shield_regeneration)
            VALUES (:player_id, :current_health, :max_health, :current_energy, :crit_chance, :crit_damage_bonus, 
            :anti_crit_chance, :anti_crit_damage, :dodge_chance, :anti_dodge_chance, :counter_attack_chance, :parry_chance, 
            :block_chance, :armor_penetration, :physical_attack, :magical_attack, :magic_resistance, :physical_resistance, 
            :mana_cost_reduction, :regen_health_rate, :energy_regeneration_bonus, :energy_pool_bonus, :absorption_bonus, 
            :shield_value, :shield_regeneration)
        """)
        await db_session.execute(query, {"player_id": player_id, **status_data})
        await db_session.commit()
        return {"status": "success", "message": f"Статус `{player_id}` добавлен"}

    elif action == "get" and player_id:
        query = text("SELECT * FROM character_status WHERE player_id = :player_id")
        result = await db_session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Статус не найден"}

    elif action == "update" and player_id and status_data:
        updates = ", ".join(f"{key} = :{key}" for key in status_data.keys())
        query = text(f"""
            UPDATE character_status SET {updates} WHERE player_id = :player_id
        """)
        await db_session.execute(query, {"player_id": player_id, **status_data})
        await db_session.commit()
        return {"status": "success", "message": f"Статус `{player_id}` обновлён"}

    elif action == "delete" and player_id:
        query = text("DELETE FROM character_status WHERE player_id = :player_id")
        await db_session.execute(query, {"player_id": player_id})
        await db_session.commit()
        return {"status": "success", "message": f"Статус `{player_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}
