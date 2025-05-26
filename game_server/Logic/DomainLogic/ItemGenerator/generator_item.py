import asyncio


from game_server.services.logging.logging_setup import logger
  # Используем глобальный логер

# Формирование шаблона предмета
def build_item_template(material, base_item, suffix=None, modifiers_defaults=None):
    name_parts = [material['prefix'], base_item['item_name']]
    effect_description = ""

    if suffix:
        name_parts.append(suffix['fragment'])
        effect_description = suffix.get("fragment", "")

    item_name = " ".join(name_parts)
    item_code = base_item['base_item_code']
    mod_map = modifiers_defaults.get(item_code, {}) if modifiers_defaults else {}

    template = {
        "name": item_name,
        "color": material['color'],
        "rarity": material['id'],
        "is_fragile": material['is_fragile'],
        "strength_percentage": material['strength_percentage'],
        "base_item_code": item_code,
        "suffix_code": 1000 if suffix is None else suffix["suffix_code"],
        "effect_description": effect_description,
    }

    if base_item['category'] == 'weapon':
        template.update({
            "p_atk": mod_map.get(11, 0),
            "m_atk": mod_map.get(12, 0),
            "armor_penetration": mod_map.get(15, 0),
            "accuracy": mod_map.get(16, 0),
            "durability": base_item['base_durability'],
            "hp_steal_percent": mod_map.get(25, 0),
        })
    elif base_item['category'] == 'armor':
        template.update({
            "physical_defense": mod_map.get(11, 0),
            "magical_defense": mod_map.get(12, 0),
            "durability": base_item['base_durability'],
            "weight": mod_map.get(15, 0),
            "dodge_chance": mod_map.get(16, 0),
        })
    elif base_item['category'] == 'accessory':
        template.update({
            "energy_pool_bonus": mod_map.get(11, 0),
            "regen_energy_rate": mod_map.get(12, 0),
            "magic_defense_bonus": mod_map.get(15, 0),
            "absorption_bonus": mod_map.get(16, 0),
            "reflect_damage": mod_map.get(24, 0),
            "damage_boost": mod_map.get(25, 0),
        })

    if suffix:
        for i in range(1, 5):
            mod_code = suffix.get(f"mod{i}_code")
            mod_value = suffix.get(f"mod{i}_value")
            if mod_code and mod_value:
                if mod_code in template:
                    template[mod_code] += mod_value

    logger.debug(f"Создан шаблон предмета: {template['name']} ({template['base_item_code']})")
    return template

# Сохранение данных с логами
async def save_items_batch(conn, table_name, items):
    success, errors = 0, 0
    first_error = None

    logger.info(f"Начинается сохранение предметов в таблицу {table_name}. Всего предметов: {len(items)}")
    

    
    for item in items:
        try:
            # Проверяем, существует ли предмет с таким именем
            existing_item = await fetch_all(conn, f"SELECT * FROM {table_name} WHERE name = '{item['name']}'")

            # Если предмет уже есть в базе и его параметры не изменились, пропускаем обновление
            if existing_item and existing_item[0] == item:
                logger.debug(f"Запись '{item['name']}' уже актуальна, пропускаем обновление")
                continue  # Пропускаем итерацию, не обновляем предмет

            # Выполняем обновление только если данные изменились или предмет новый
            await upsert_data(conn, table_name, "name", item)
            success += 1

        except Exception as e:
            errors += 1
            if not first_error:
                first_error = str(e)

    logger.info(f"[{table_name}] Сохранение завершено: Успешно: {success}, Ошибок: {errors}")
    if first_error:
        logger.error(f"[{table_name}] Первая ошибка: {first_error}")


# Генерация предметов для категории
async def generate_templates_by_category(conn, category: str, table_name: str):
    logger.info(f"Генерация предметов категории '{category}' начата")

    base_items = await get_base_items_by_category(conn, category)
    suffixes = await get_suffixes_by_type(conn, category)
    materials = await fetch_all(conn, "SELECT * FROM materials")
    template_defaults = await load_template_modifier_defaults(conn)

    logger.info(f"Найдено материалов: {len(materials)}, базовых предметов: {len(base_items)}, суффиксов: {len(suffixes)}")

    items = []

    for material in materials:
        for base_item in base_items:
            if material['id'] < 9:
                items.append(build_item_template(material, base_item, None, template_defaults))
            else:
                for suffix in suffixes:
                    items.append(build_item_template(material, base_item, suffix, template_defaults))

    await save_items_batch(conn, table_name, items)
    logger.info(f"Генерация предметов категории '{category}' завершена")

# Точки входа
def generate_weapon_templates(conn):
    return generate_templates_by_category(conn, "weapon", "weapon_templates")

def generate_armor_templates(conn):
    return generate_templates_by_category(conn, "armor", "armor_templates")

def generate_accessory_templates(conn):
    return generate_templates_by_category(conn, "accessory", "accessory_templates")
