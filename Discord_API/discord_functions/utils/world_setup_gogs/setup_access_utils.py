from collections import defaultdict
import discord
from typing import Dict, List, Any, Optional, Set, Tuple
from Discord_API.api_route_function.spec_route.discord_bindings_api import get_all_discord_bindings_api
from Discord_API.api_route_function.spec_route.state_entities_discord_api import get_all_entities_discord
from Discord_API.api_route_function.system.system_gameworld_api import get_subregions
from Discord_API.api_route_function.system.system_mapping_api import get_all_entities
from Discord_API.config.logging.logging_setup import logger
from Discord_API.constant import constants_world



# --- Настройки разрешений по умолчанию ---
# Эти права будут применяться к @everyone и к основным ролям (кроме админов)


async def _fetch_and_process_raw_data(guild_id: int) -> Dict[str, List[Any]]:
    """
    Получает все необходимые данные от API и предварительно их обрабатывает,
    гарантируя, что они возвращаются в формате списков.
    """
    logger.info("⚡️ Получаем сырые данные от game_server API...")
    
    discord_bindings_raw = []
    subregions_raw = []
    entities_discord_raw = []
    all_entities_raw = []

    try:
        print("\n--- Начало получения данных из API ---")

        print(f"Вызов get_all_discord_bindings_api({guild_id})...")
        discord_bindings_raw = await get_all_discord_bindings_api(guild_id)
        print(f"Сырые discord_bindings_raw (тип: {type(discord_bindings_raw)}): {discord_bindings_raw}")

        print("Вызов get_subregions()...")
        subregions_raw = await get_subregions()
        print(f"Сырые subregions_raw (тип: {type(subregions_raw)}): {subregions_raw}")

        print(f"Вызов get_all_entities_discord({guild_id})...")
        entities_discord_raw = await get_all_entities_discord(guild_id)
        print(f"Сырые entities_discord_raw (тип: {type(entities_discord_raw)}): {entities_discord_raw}")

        print("Вызов get_all_entities()...")
        all_entities_raw = await get_all_entities()
        print(f"Сырые all_entities_raw (тип: {type(all_entities_raw)}): {all_entities_raw}")
        print("--- Все API вызовы выполнены ---")

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных от game_server API: {e}", exc_info=True)
        print(f"ОШИБКА API: {e}. Возвращаем пустые списки.")
        return {
            "discord_bindings": [],
            "subregions": [],
            "entities_discord": [],
            "all_entities": []
        }

    print("\n--- Обработка сырых данных в списки ---")
    # Преобразуем ответы API в списки, если они обернуты в {"data": [...]}.
    # Это предотвращает ошибку "'list' object has no attribute 'get'".
    
    processed_discord_bindings = discord_bindings_raw if isinstance(discord_bindings_raw, list) else discord_bindings_raw.get("data", [])
    print(f"Обработанные discord_bindings (тип: {type(processed_discord_bindings)}): {processed_discord_bindings}")

    processed_subregions = subregions_raw if isinstance(subregions_raw, list) else subregions_raw.get("data", [])
    print(f"Обработанные subregions (тип: {type(processed_subregions)}): {processed_subregions}")

    processed_entities_discord = entities_discord_raw if isinstance(entities_discord_raw, list) else entities_discord_raw.get("data", [])
    print(f"Обработанные entities_discord (тип: {type(processed_entities_discord)}): {processed_entities_discord}")

    processed_all_entities = all_entities_raw if isinstance(all_entities_raw, list) else all_entities_raw.get("data", [])
    print(f"Обработанные all_entities (тип: {type(processed_all_entities)}): {processed_all_entities}")
    print("--- Обработка данных завершена ---")

    logger.info("✅ Сырые данные API успешно получены и обработаны.")
    
    final_data = {
        "discord_bindings": processed_discord_bindings,
        "subregions": processed_subregions,
        "entities_discord": processed_entities_discord,
        "all_entities": processed_all_entities
    }
    print(f"\n--- Окончательные данные, возвращаемые _fetch_and_process_raw_data ---")
    for key, value in final_data.items():
        print(f"  {key}: {value[:5]}... ({len(value)} элементов)") # Выводим первые 5 элементов для краткости
    print("--------------------------------------------------")
    return final_data




def _extract_system_roles(processed_entities_discord: List[Dict[str, Any]]) -> Dict[str, Optional[int]]:
    """
    Извлекает ID системных ролей (админ, модератор, тестер, онлайн, оффлайн)
    из обработанных данных сущностей Discord.
    """
    logger.info("⚡️ Извлекаем ID системных ролей...")
    
    admin_role_ids: List[int] = []
    tester_role_id: Optional[int] = None
    online_role_id: Optional[int] = None
    offline_role_id: Optional[int] = None

    for entity_binding in processed_entities_discord:
        if not isinstance(entity_binding, dict):
            logger.warning(f"Пропущен не-словарь элемент при извлечении системных ролей: {entity_binding}")
            continue
        
        access_code = entity_binding.get("access_code")
        role_id = entity_binding.get("role_id")
        
        if role_id is None or not isinstance(role_id, int):
            logger.warning(f"Пропущен элемент с некорректным 'role_id' при извлечении системных ролей: {entity_binding}")
            continue

        if access_code == 1:  # Admin
            admin_role_ids.append(role_id)
        elif access_code == 2:  # Moderator
            admin_role_ids.append(role_id) # Модератор также получает полный доступ
        elif access_code == 3:  # Тестер
            tester_role_id = role_id
        elif access_code == 101: # Online
            online_role_id = role_id
        elif access_code == 102: # Offline
            offline_role_id = role_id

    logger.info(f"Определены админские роли (ID): {admin_role_ids}")
    logger.info(f"Определена роль Тестер (ID): {tester_role_id}")
    logger.info(f"Определена роль Online (ID): {online_role_id}")
    logger.info(f"Определена роль Offline (ID): {offline_role_id}")

    # Логирование предупреждений, если ключевые роли не найдены
    if not admin_role_ids:
        logger.warning("⚠️ Не определены админские роли (access_code 1 или 2). Убедитесь, что они привязаны к Discord ролям.")
    if not tester_role_id:
        logger.warning("⚠️ Не определена роль Тестер (access_code 3). Убедитесь, что она привязана к Discord роли.")
    if not offline_role_id:
        logger.warning("⚠️ Не определена роль 'Offline' (access_code 102). Убедитесь, что она привязана к Discord роли.")
    if not online_role_id:
        logger.warning("⚠️ Не определена роль 'Online' (access_code 101). Убедитесь, что она привязана к Discord роли.")
    
    return {
        "admin_role_ids": admin_role_ids,
        "tester_role_id": tester_role_id,
        "online_role_id": online_role_id,
        "offline_role_id": offline_role_id,
    }


def _map_game_access_keys(
    processed_subregions: List[Dict[str, Any]],
    processed_entities_discord: List[Dict[str, Any]] # Теперь entities_discord - главный источник
) -> Dict[str, Any]:
    """
    Формирует карты, связывающие access_key игровых локаций с их названиями,
    а также access_key локаций со списками требуемых Discord Role ID.
    
    Использует processed_entities_discord как основной источник валидных игровых access_key
    для привязки к Discord ролям.
    """
    logger.info("⚡️ Формируем карты для Access Keys игровых локаций и Discord ролей...")

    access_key_to_name: Dict[int, str] = {}
    valid_game_access_keys: Set[int] = set()
    
    # 1. Собираем все валидные access_key и их имена из *processed_entities_discord*
    # Это включает как системные access_code, так и access_code игровых локаций/регионов.
    for entity in processed_entities_discord:
        if isinstance(entity, dict):
            access_code = entity.get("access_code")
            role_name = entity.get("role_name") # Используем role_name как название для access_key
            
            if access_code is not None and isinstance(access_code, int) and role_name is not None:
                access_key_to_name[access_code] = role_name # access_code теперь сопоставляем с role_name
                valid_game_access_keys.add(access_code)
            else:
                logger.warning(f"Некорректные данные в processed_entities_discord для access_key/названия: {entity}. Пропускаем.")
        else:
            logger.warning(f"Пропущен не-словарь элемент в processed_entities_discord: {entity}")

    # 2. Дополняем (или перезаписываем) названия из *subregions*
    # subregions могут содержать более точные или предпочтительные названия для субрегионов
    for sr in processed_subregions:
        if isinstance(sr, dict):
            access_key_str = sr.get("access_key")
            subregion_name = sr.get("subregion_name")
            
            if access_key_str is not None and subregion_name is not None:
                try:
                    ak_int = int(access_key_str)
                    # Если subregion_name есть, используем его как более точное название
                    access_key_to_name[ak_int] = subregion_name 
                    valid_game_access_keys.add(ak_int) # Убедимся, что субрегионы тоже валидные access_key
                except ValueError:
                    logger.warning(f"Не удалось преобразовать access_key '{access_key_str}' в число из subregions. Пропускаем.")
            else:
                logger.warning(f"Сущность в subregions не содержит 'access_key' или 'subregion_name': {sr}")
        else:
            logger.warning(f"Пропущен не-словарь элемент в processed_subregions: {sr}")

    logger.debug(f"Все валидные Access Keys (собраны из entities_discord и subregions): {valid_game_access_keys}")
    logger.debug(f"Карта Access Key (int) -> Name: {access_key_to_name}")

    # 3. Карта: Access Key локации (int) -> Список Discord Role IDs (List[int])
    required_roles_for_access_key: Dict[int, List[int]] = defaultdict(list)
    SYSTEM_ACCESS_CODES = {1, 2, 3, 101, 102} # Admin, Moderator, Tester, Online, Offline

    for entity in processed_entities_discord:
        if isinstance(entity, dict):
            access_code = entity.get("access_code")
            role_id = entity.get("role_id")
            
            if (access_code is not None and 
                isinstance(access_code, int) and
                access_code not in SYSTEM_ACCESS_CODES and # Исключаем системные access_code
                role_id is not None and 
                isinstance(role_id, int)):
                
                # Теперь эта проверка должна почти всегда проходить,
                # так как valid_game_access_keys содержит access_code из entities_discord.
                if access_code in valid_game_access_keys:
                    required_roles_for_access_key[access_code].append(role_id)
                else:
                    # Это предупреждение теперь будет очень редким,
                    # если данные консистентны.
                    logger.warning(f"Сущность Discord (role_id: {role_id}) привязана к access_key '{access_code}', который не был найден среди валидных игровых локаций. Пропускаем эту привязку для ролей локаций.")
            else:
                if (access_code is not None and 
                    isinstance(access_code, int) and 
                    access_code in SYSTEM_ACCESS_CODES):
                    logger.debug(f"Пропущена системная роль (access_code: {access_code}) из карты 'required_roles_for_access_key'.")
                else:
                    logger.warning(f"Некорректные данные в processed_entities_discord для карты ролей: {entity}. Пропускаем.")
        else:
            logger.warning(f"Пропущен не-словарь элемент в processed_entities_discord: {entity}")

    logger.debug(f"Карта Access Key (int) -> Discord Role IDs для локаций: {required_roles_for_access_key}")
    logger.info("✅ Карты Access Keys игровых локаций и Discord ролей сформированы.")

    return {
        "access_key_to_name": access_key_to_name,
        "valid_game_access_keys": valid_game_access_keys,
        "required_roles_for_access_key": required_roles_for_access_key,
    }



def _map_discord_channels_to_access_keys(
    processed_discord_bindings: List[Dict[str, Any]],
    valid_game_access_keys: Set[int]
) -> Dict[str, Dict[int, int]]:
    """
    Формирует карты, связывающие Discord Category ID и Channel ID с их соответствующими
    Access Keys регионов/локаций.
    """
    logger.info("⚡️ Формируем карты Discord ID к Access Keys регионов...")

    discord_category_id_to_access_key: Dict[int, int] = {}
    discord_channel_id_to_access_key: Dict[int, int] = {}

    for binding in processed_discord_bindings:
        if not isinstance(binding, dict):
            logger.warning(f"Пропущен не-словарь элемент в processed_discord_bindings: {binding}")
            continue

        access_key_str = binding.get("access_key") # Это access_key региона из вашего API
        category_id = binding.get("category_id")
        channel_id = binding.get("channel_id")

        if access_key_str is None:
            logger.debug(f"Пропущен биндинг без access_key: {binding}")
            continue

        try:
            bound_access_key_int = int(access_key_str)
        except ValueError:
            logger.warning(f"Не удалось преобразовать access_key '{access_key_str}' в число из Discord-биндинга. Пропускаем биндинг: {binding}")
            continue

        # Валидация: убедимся, что access_key из биндинга существует среди валидных ключей регионов
        if bound_access_key_int not in valid_game_access_keys:
            logger.warning(f"Биндинг с невалидным/неизвестным access_key региона '{bound_access_key_int}' для Discord ID {category_id or channel_id}. Пропускаем биндинг: {binding}")
            continue

        # Привязываем Discord ID к Access Key региона
        if channel_id is not None:
            if isinstance(channel_id, int):
                discord_channel_id_to_access_key[channel_id] = bound_access_key_int
            else:
                logger.warning(f"Некорректный channel_id (не int): {channel_id} для биндинга: {binding}")
        elif category_id is not None: # Если channel_id null, но category_id есть
            if isinstance(category_id, int):
                discord_category_id_to_access_key[category_id] = bound_access_key_int
            else:
                logger.warning(f"Некорректный category_id (не int): {category_id} для биндинга: {binding}")
        else:
            logger.warning(f"Биндинг не содержит ни channel_id, ни category_id. Пропускаем: {binding}")

    logger.debug(f"Карта Discord Category ID (int) -> Access Key региона (int): {discord_category_id_to_access_key}")
    logger.debug(f"Карта Discord Channel ID (int) -> Access Key региона (int): {discord_channel_id_to_access_key}")
    logger.info("✅ Карты Discord ID к Access Keys регионов сформированы.")

    return {
        "discord_category_id_to_access_key": discord_category_id_to_access_key,
        "discord_channel_id_to_access_key": discord_channel_id_to_access_key,
    }


# --- Вспомогательная функция 1: Подготовка всех данных для обработки ---
async def _prepare_data_for_processing(
    guild: discord.Guild,
    api_data: Dict[str, List[Any]]
) -> Tuple[
    Dict[int, Dict[str, Any]],     # subregions_map
    Dict[int, int],                 # access_code_to_discord_role_id_map
    Dict[str, discord.Role],        # system_roles_map
    Dict[int, int],                 # discord_entity_to_access_key_map
    List[discord.Role]              # all_roles_on_guild
]:
    """
    Обрабатывает сырые данные API, формируя маппинги и получая объекты Discord ролей.
    """
    logger.info("⚡️ Подготавливаем данные для обработки...")

    subregions_map: Dict[int, Dict[str, Any]] = {
        int(sr["access_key"]): sr
        for sr in api_data.get("subregions", [])
        if sr.get("access_key") is not None
    }
    logger.debug(f"subregions_map инициализирована с {len(subregions_map)} записями.")

    all_roles_on_guild = await guild.fetch_roles()
    logger.debug(f"Получены все роли с сервера Discord: {len(all_roles_on_guild)} ролей.")

    access_code_to_discord_role_id_map: Dict[int, int] = {}
    system_roles_map: Dict[str, discord.Role] = {}

    for entity in api_data.get("entities_discord", []):
        if entity.get("access_code") is not None and entity.get("role_id") is not None:
            try:
                access_code = int(entity["access_code"])
                role_id = int(entity["role_id"])
                access_code_to_discord_role_id_map[access_code] = role_id

                role_name_lower = entity.get("role_name", "").lower()
                system_key = constants_world.ROLE_NAME_MAPPING.get(role_name_lower)

                if system_key in [
                    constants_world.SYSTEM_ROLE_KEY_ADMIN,
                    constants_world.SYSTEM_ROLE_KEY_MODERATOR,
                    constants_world.SYSTEM_ROLE_KEY_ONLINE,
                    constants_world.SYSTEM_ROLE_KEY_OFFLINE,
                    constants_world.SYSTEM_ROLE_KEY_TESTER,
                    constants_world.SYSTEM_ROLE_KEY_CHARACTER_SELECTION 
                ]:
                    role_obj = discord.utils.get(all_roles_on_guild, id=role_id)
                    if role_obj:
                        system_roles_map[system_key] = role_obj
                        logger.debug(f"Системная роль '{system_key}' ({role_obj.name}) добавлена в system_roles_map.")
                    else:
                        logger.warning(f"Системная роль с ID {role_id} и именем '{role_name_lower}' не найдена на сервере. Пропускаем.")
            except ValueError:
                logger.warning(f"Некорректный access_code или role_id в entities_discord: {entity}. Пропускаем.")
    logger.debug(f"access_code_to_discord_role_id_map инициализирована с {len(access_code_to_discord_role_id_map)} записями.")
    logger.debug(f"system_roles_map инициализирована с {len(system_roles_map)} записями.")

    discord_entity_to_access_key_map: Dict[int, int] = {}
    for binding in api_data.get("discord_bindings", []):
        access_key = binding.get("access_key")
        if access_key is None:
            logger.warning(f"Привязка без 'access_key' для Discord ID {binding.get('category_id') or binding.get('channel_id')}. Пропускаем.")
            continue
        try:
            ak_int = int(access_key)
            if binding.get("category_id") is not None:
                discord_entity_to_access_key_map[int(binding["category_id"])] = ak_int
            if binding.get("channel_id") is not None:
                discord_entity_to_access_key_map[int(binding["channel_id"])] = ak_int
        except ValueError:
            logger.warning(f"Некорректный ID или access_key в discord_bindings: {binding}. Пропускаем.")
    logger.debug(f"discord_entity_to_access_key_map инициализирована с {len(discord_entity_to_access_key_map)} записями.")

    logger.info("✅ Подготовка данных для обработки завершена.")
    return subregions_map, access_code_to_discord_role_id_map, system_roles_map, discord_entity_to_access_key_map, all_roles_on_guild

# --- Вспомогательная функция 2: Сбор объектов Discord и их зависимостей ---
async def _collect_discord_objects_and_inheritances(
    guild: discord.Guild,
    subregions_map: Dict[int, Dict[str, Any]],
    discord_entity_to_access_key_map: Dict[int, int],
    access_code_to_discord_role_id_map: Dict[int, int],
    system_roles_map: Dict[str, discord.Role] # Добавляем system_roles_map для доступа к online_role
) -> Tuple[List[discord.abc.GuildChannel], Dict[int, Set[int]]]:
    """
    Собирает все каналы и категории сервера и определяет, какие роли каналы
    передают своим родительским категориям.
    """
    logger.info(f"⚡️ Собираем объекты сервера и их зависимости для '{guild.name}'...")
    discord_objects_to_update: List[discord.abc.GuildChannel] = []
    category_inherited_roles: Dict[int, Set[int]] = defaultdict(set)

    online_role_id_from_system = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_ONLINE).id if system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_ONLINE) else None

    for discord_object in guild.channels:
        discord_objects_to_update.append(discord_object)

        if isinstance(discord_object, (discord.TextChannel, discord.VoiceChannel)):
            channel_access_key = discord_entity_to_access_key_map.get(discord_object.id)
            if channel_access_key and channel_access_key in subregions_map:
                subregion_data = subregions_map[channel_access_key]
                subregion_access_code_for_role = subregion_data.get("access_code")

                if subregion_access_code_for_role is not None:
                    try:
                        subregion_access_code_int = int(subregion_access_code_for_role)
                        required_role_id = access_code_to_discord_role_id_map.get(subregion_access_code_int)

                        # Если роль не найдена, но access_code в публичном диапазоне,
                        # и у нас есть ID роли "Онлайн", используем его для наследования.
                        if not required_role_id and \
                           constants_world.PUBLIC_ACCESS_CODES_START <= subregion_access_code_int <= constants_world.PUBLIC_ACCESS_CODES_END:
                            if online_role_id_from_system:
                                required_role_id = online_role_id_from_system
                                logger.debug(f"Канал '{discord_object.name}' (access_key: {channel_access_key}) публичный, назначаем 'Онлайн' для наследования.")
                            else:
                                logger.warning(f"Роль 'Онлайн' не найдена в system_roles_map, не можем назначить её публичному каналу '{discord_object.name}' для наследования.")

                        if required_role_id:
                            if discord_object.category:
                                category_inherited_roles[discord_object.category.id].add(required_role_id)
                                logger.debug(
                                    f"Канал '{discord_object.name}' (access_key: {channel_access_key}) "
                                    f"передал роль с ID {required_role_id} категории '{discord_object.category.name}'."
                                )
                        else:
                            logger.warning(
                                f"Для access_code {subregion_access_code_int} (исходная строка: '{subregion_access_code_for_role}') "
                                f"канала '{discord_object.name}' "
                                f"не найден Discord Role ID в entities_discord (или не удалось получить 'Онлайн' для публичного). "
                                f"Пропускаем наследование этой роли."
                            )
                    except ValueError:
                        logger.error(
                            f"Ошибка преобразования access_code '{subregion_access_code_for_role}' "
                            f"из subregions в целое число для канала '{discord_object.name}'. Пропускаем наследование."
                        )
                else:
                    logger.warning(
                        f"Канал '{discord_object.name}' (access_key: {channel_access_key}) не имеет 'access_code' в subregions_map. Не передает роли категории."
                    )
            else:
                logger.debug(
                    f"Канал '{discord_object.name}' ({discord_object.id}) не привязан к известному субрегиону или не имеет access_key. Не передает роли категории."
                )
    logger.info(f"✅ Сбор объектов сервера и зависимостей завершен. Найдено {len(discord_objects_to_update)} объектов для обновления.")
    return discord_objects_to_update, category_inherited_roles




async def _generate_overwrites_for_objects(
    guild: discord.Guild,
    discord_objects_to_update: List[discord.abc.GuildChannel],
    discord_entity_to_access_key_map: Dict[int, int],
    subregions_map: Dict[int, Dict[str, Any]],
    access_code_to_discord_role_id_map: Dict[int, int],
    system_roles_map: Dict[str, discord.Role],
    category_inherited_roles: Dict[int, Set[int]],
    all_roles_on_guild: List[discord.Role] # Список всех ролей на гильдии для discord.utils.get
) -> Dict[int, Dict[discord.Role, discord.PermissionOverwrite]]:
    """
    Генерирует объект перезаписи разрешений (PermissionOverwrite) для каждого канала или категории,
    основываясь на их access_key и системных ролях.

    Эта функция реализует логику: "по умолчанию всё запрещено, затем явно разрешается только нужное".
    Роли действуют как статусные флаги, а основные права выдаются на уровне каналов/категорий.

    Args:
        guild: Объект discord.Guild, представляющий сервер.
        discord_objects_to_update: Список объектов Discord (каналов или категорий), для которых
                                   нужно сгенерировать разрешения.
        discord_entity_to_access_key_map: Словарь, сопоставляющий ID сущностей Discord (каналов/категорий)
                                          с их access_key из API.
        subregions_map: Словарь с данными о субрегионах, используемый для определения прав
                        для каналов, привязанных к кастомным ролям.
        access_code_to_discord_role_id_map: Словарь, сопоставляющий access_code из subregions
                                            с ID соответствующих ролей Discord.
        system_roles_map: Словарь системных ролей (Admin, Moderator, Online, Offline, Tester, Character Selection),
                          полученных из Discord API и сопоставленных по ключу.
        category_inherited_roles: Словарь {category_id: set[role_id]}, содержащий ID ролей,
                                  которые должны видеть категорию, так как они имеют доступ к её дочерним каналам.
        all_roles_on_guild: Список всех объектов discord.Role на сервере, необходимый для
                            поиска ролей по ID с помощью discord.utils.get.

    Returns:
        Словарь, где ключ - ID объекта Discord (канала/категории), а значение -
        словарь PermissionOverwrite, готовый для установки.
    """
    
    final_overwrites_map: Dict[int, Dict[discord.Role, discord.PermissionOverwrite]] = defaultdict(dict)

    # Получаем системные роли для удобства доступа
    offline_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_OFFLINE)
    online_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_ONLINE)
    character_selection_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_CHARACTER_SELECTION)
    tester_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_TESTER)
    admin_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_ADMIN)
    moderator_role = system_roles_map.get(constants_world.SYSTEM_ROLE_KEY_MODERATOR)

    # Определяем объекты PermissionOverwrite из констант для удобства и читаемости
    PERMS_DENY_ALL = discord.PermissionOverwrite(**constants_world.DEFAULT_DENY_PERMISSIONS)
    PERMS_VIEW_ONLY = discord.PermissionOverwrite(**constants_world.DEFAULT_ALLOW_READ_ONLY_PERMISSIONS)
    PERMS_INTERACT = discord.PermissionOverwrite(**constants_world.DEFAULT_ALLOW_BUTTON_INTERACTION_PERMISSIONS)
    PERMS_ADMIN_FULL_ACCESS = discord.PermissionOverwrite(**constants_world.DEFAULT_ALLOW_FULL_PERMISSIONS)

    for discord_object in discord_objects_to_update:
        current_overwrites: Dict[discord.Role, discord.PermissionOverwrite] = {}

        # --- Шаг 1: Базовые и обязательные права для каждого объекта ---

        # 1. Запрещаем все для @everyone по умолчанию (политика "запрещено по умолчанию")
        if guild.default_role:
            current_overwrites[guild.default_role] = PERMS_DENY_ALL
            logger.debug(f"Для '{discord_object.name}' (ID: {discord_object.id}) установлен DENY ALL для @everyone.")

        # 2. Разрешаем полный доступ для админов и модераторов (они всегда могут всё)
        if admin_role:
            current_overwrites[admin_role] = PERMS_ADMIN_FULL_ACCESS
            logger.debug(f"Для '{discord_object.name}': разрешен полный доступ для Admin.")
        else:
            logger.warning(f"Роль Admin не найдена в system_roles_map. Проверьте настройки.")
        
        if moderator_role:
            current_overwrites[moderator_role] = PERMS_ADMIN_FULL_ACCESS
            logger.debug(f"Для '{discord_object.name}': разрешен полный доступ для Moderator.")
        else:
            logger.warning(f"Роль Moderator не найдена в system_roles_map. Проверьте настройки.")
        
        # --- Шаг 2: Применяем логику в зависимости от типа объекта Discord (Категория vs Канал) ---
        if isinstance(discord_object, discord.CategoryChannel):
            # --- Логика для Категорий: Только видимость для навигации ---
            logger.info(f"Настройка прав для категории '{discord_object.name}' (ID: {discord_object.id}).")

            # Системные роли: сначала DENY ALL, затем специфические ALLOW VIEW_ONLY
            # Offline и Character Selection должны видеть категории для навигации к своим каналам
            if offline_role:
                current_overwrites[offline_role] = PERMS_VIEW_ONLY
                logger.debug(f"Категория '{discord_object.name}': разрешен VIEW_ONLY для Offline.")
            
            if character_selection_role:
                current_overwrites[character_selection_role] = PERMS_VIEW_ONLY
                logger.debug(f"Категория '{discord_object.name}': разрешен VIEW_ONLY для Character Selection.")
            
            # Online и Tester по умолчанию DENY ALL в категориях, если нет других причин для видимости
            if online_role:
                current_overwrites[online_role] = PERMS_DENY_ALL
                logger.debug(f"Категория '{discord_object.name}': DENY ALL для Online.")
            
            if tester_role:
                current_overwrites[tester_role] = PERMS_DENY_ALL
                logger.debug(f"Категория '{discord_object.name}': DENY ALL для Tester.")

            # Унаследованные роли: те, которые имеют доступ к каналам внутри этой категории,
            # должны видеть саму категорию (только VIEW_ONLY).
            inherited_role_ids = category_inherited_roles.get(discord_object.id, set())
            for inherited_role_id in inherited_role_ids:
                inherited_role = discord.utils.get(all_roles_on_guild, id=inherited_role_id)
                if inherited_role:
                    current_overwrites[inherited_role] = PERMS_VIEW_ONLY
                    logger.debug(f"Категория '{discord_object.name}': унаследовано VIEW_ONLY для роли '{inherited_role.name}' (ID: {inherited_role_id}).")
                else:
                    logger.warning(f"Унаследованная роль с ID {inherited_role_id} не найдена на сервере для категории '{discord_object.name}'. Пропускаем.")

        elif isinstance(discord_object, (discord.TextChannel, discord.VoiceChannel)):
            # --- Логика для Каналов: Интерактивные права ---
            logger.info(f"Настройка прав для канала '{discord_object.name}' (ID: {discord_object.id}).")
            channel_access_key = discord_entity_to_access_key_map.get(discord_object.id)

            # Шаг 2.1: По умолчанию запрещаем всем системным ролям (кроме Admin/Mod/everyone)
            # Это создаёт "чистый лист" для последующих явных разрешений.
            roles_to_default_deny_on_channel = [
                offline_role, online_role, character_selection_role, tester_role
            ]
            for role in roles_to_default_deny_on_channel:
                if role: # Убедимся, что роль существует
                    current_overwrites[role] = PERMS_DENY_ALL
                    logger.debug(f"Канал '{discord_object.name}': роль '{role.name}' по умолчанию DENY ALL.")

            # Шаг 2.2: Применяем специфические разрешения по Access Key (приоритетные кейсы)
            # ВАЖНО: Порядок проверки здесь критичен. Специфичные кейсы идут первыми.
            
            # Кейс 1: 🎮 Игровое лобби (access_key: 102) - для Offline роли
            if channel_access_key == constants_world.SYSTEM_ACCESS_CODE_OFFLINE:
                if offline_role:
                    current_overwrites[offline_role] = PERMS_INTERACT
                    logger.info(f"Канал '{discord_object.name}': разрешен INTERACT для роли 'Offline' (access_key: {channel_access_key}).")
                else:
                    logger.warning(f"Канал '{discord_object.name}' (access_key: {channel_access_key}): роль 'Offline' не найдена. Права не назначены.")

            # Кейс 2: 👤 Выбор персонажа (access_key: 4) - для Character Selection роли
            elif channel_access_key == constants_world.SYSTEM_ACCESS_CODE_CHARACTER_SELECTION:
                if character_selection_role:
                    current_overwrites[character_selection_role] = PERMS_INTERACT
                    logger.info(f"Канал '{discord_object.name}': разрешен INTERACT для роли 'Character Selection' (access_key: {channel_access_key}).")
                else:
                    logger.warning(f"Канал '{discord_object.name}' (access_key: {channel_access_key}): роль 'Character Selection' не найдена. Права не назначены.")

            # Кейс 3: Основные игровые каналы (access_key: 101) - для Online роли
            elif channel_access_key == constants_world.SYSTEM_ACCESS_CODE_ONLINE:
                if online_role:
                    current_overwrites[online_role] = PERMS_INTERACT
                    logger.info(f"Канал '{discord_object.name}': разрешен INTERACT для роли 'Online' (access_key: {channel_access_key}).")
                else:
                    logger.warning(f"Канал '{discord_object.name}' (access_key: {channel_access_key}): роль 'Online' не найдена. Права не назначены.")

            # Кейс 4: Каналы с кастомными ролями через subregions_map (access_key в subregions_map)
            # Это включает ваши access_key типа 2001, 3001, 4001, 20003, если они есть в subregions_map
            elif channel_access_key is not None and channel_access_key in subregions_map:
                subregion_data = subregions_map[channel_access_key]
                subregion_access_code_for_role = subregion_data.get("access_code")

                if subregion_access_code_for_role is not None:
                    try:
                        subregion_access_code_int = int(subregion_access_code_for_role)
                        required_role_id = access_code_to_discord_role_id_map.get(subregion_access_code_int)

                        # Специальный кейс для публичных access_code (получают роль "Онлайн")
                        # Это сработает, если access_code из subregions_map находится в публичном диапазоне
                        if not required_role_id and \
                           constants_world.PUBLIC_ACCESS_CODES_START <= subregion_access_code_int <= constants_world.PUBLIC_ACCESS_CODES_END:
                            if online_role:
                                required_role_id = online_role.id
                                logger.debug(f"Для access_code {subregion_access_code_int} (публичный диапазон) канала '{discord_object.name}' назначена роль 'Online'.")
                            else:
                                logger.warning(f"Роль 'Online' не найдена в system_roles_map для назначения публичным каналам '{discord_object.name}'.")

                        if required_role_id:
                            required_role = discord.utils.get(all_roles_on_guild, id=required_role_id)
                            if required_role:
                                current_overwrites[required_role] = PERMS_INTERACT
                                logger.info(f"Сформированы права для канала '{discord_object.name}'. Разрешена INTERACT роль: '{required_role.name}' (ID: {required_role_id}).")
                            else:
                                logger.warning(f"Требуемая роль с ID {required_role_id} не найдена на сервере для канала '{discord_object.name}'. Права не назначены.")
                        else:
                            logger.warning(f"Для access_code {subregion_access_code_int} канала '{discord_object.name}' не найден Discord Role ID (или не публичный диапазон без привязки). Пропускаем.")
                    except ValueError:
                        logger.error(f"Ошибка преобразования access_code '{subregion_access_code_for_role}' из subregions в целое число для канала '{discord_object.name}'. Права не назначены.")
                else:
                    logger.warning(f"Канал '{discord_object.name}' (access_key: {channel_access_key}) не имеет 'access_code' в subregions_map. Права не назначены.")
            
            # Кейс 5: Общий случай для остальных игровых каналов (access_key >= 10, но не попавший в предыдущие)
            # Например, если access_key >= 10, но не имеет специфической привязки через subregions_map,
            # и не является системным 101, 102, 4.
            elif channel_access_key is not None and channel_access_key >= 10:
                if online_role:
                    current_overwrites[online_role] = PERMS_INTERACT
                    logger.info(f"Канал '{discord_object.name}': разрешен INTERACT для роли 'Online' (общий игровой access_key: {channel_access_key}).")
                else:
                    logger.warning(f"Канал '{discord_object.name}' (общий игровой access_key: {channel_access_key}): роль 'Online' не найдена. Права не назначены.")

            # Кейс 6: Каналы без определённого access_key или прочие каналы
            else:
                # По умолчанию разрешаем Offline роли, если канал не привязан к чему-либо другому.
                # Это может быть канал общего назначения или стартовый, не требующий спец. роли.
                if offline_role:
                    current_overwrites[offline_role] = PERMS_INTERACT
                    logger.info(f"Канал '{discord_object.name}' ({discord_object.id}) не привязан к субрегиону/спец. access_key. Разрешен INTERACT для роли 'Offline'.")
                else:
                    logger.warning(f"Канал '{discord_object.name}' ({discord_object.id}) не привязан к субрегиону и роль 'Offline' не найдена/не назначена. Права не назначены.")
        else:
            logger.warning(f"Объект '{discord_object.name}' (ID: {discord_object.id}) имеет неизвестный тип: {type(discord_object)}. Права не будут обработаны.")

        # Сохраняем сформированные перезаписи для текущего объекта
        final_overwrites_map[discord_object.id] = current_overwrites
        logger.info(f"Завершено формирование прав для '{discord_object.name}'. Всего ролей с правами: {len(current_overwrites)}")
    
    return final_overwrites_map


# --- Главная функция-оркестратор для обновления доступа гильдии ---
async def update_guild_access(guild: discord.Guild):
    logger.info(f"Начинаем обновление доступа для сервера '{guild.name}' ({guild.id})...")

    try:
        # 1. Получаем все сырые данные из API
        api_data = await _fetch_and_process_raw_data(guild.id)
        if not isinstance(api_data, dict) or \
           not all(key in api_data for key in ["entities_discord", "subregions", "discord_bindings"]):
            logger.error(f"❌ Некорректная или неполная структура данных из API. Получено: {api_data}. Отмена обновления доступа.")
            return

        # 2. Подготавливаем все маппинги и объекты Discord ролей из данных API
        subregions_map, access_code_to_discord_role_id_map, \
        system_roles_map, discord_entity_to_access_key_map, \
        all_roles_on_guild = await _prepare_data_for_processing(guild, api_data)

        # 3. Собираем все Discord-объекты (каналы/категории) и определяем наследование ролей для категорий
        discord_objects_to_update, category_inherited_roles = \
            await _collect_discord_objects_and_inheritances(
                guild,
                subregions_map,
                discord_entity_to_access_key_map,
                access_code_to_discord_role_id_map,
                system_roles_map
            )
        
        # 4. Генерируем перезаписи прав для всех Discord-объектов
        # (Используем _generate_overwrites_for_objects, которая уже должна быть вынесена)
        final_overwrites_map = await _generate_overwrites_for_objects(
            guild,
            discord_objects_to_update,
            discord_entity_to_access_key_map,
            subregions_map,
            access_code_to_discord_role_id_map,
            system_roles_map,
            category_inherited_roles,
            all_roles_on_guild
        )

        # 5. Применяем сгенерированные перезаписи прав к каждому Discord-объекту
        logger.info(f"🚀 Начинаем применение сгенерированных прав для {len(discord_objects_to_update)} объектов...")
        
        # Сортировка для применения сначала к категориям, затем к каналам
        # Это помогает избежать потенциальных проблем с переопределением прав
        discord_objects_to_update.sort(key=lambda x: 0 if isinstance(x, discord.CategoryChannel) else 1)

        for discord_object in discord_objects_to_update:
            object_id = discord_object.id
            if object_id in final_overwrites_map:
                try:
                    # Получаем текущие перезаписи, чтобы сохранить ручные изменения, если они есть.
                    # discord.py автоматически объединяет, но явное чтение помогает понять логику.
                    current_overwrites = discord_object.overwrites
                    
                    # Применяем только те перезаписи, которые мы сгенерировали.
                    # discord.py's edit() метод будет применять наши перезаписи поверх существующих.
                    # Важно: если нужно УДАЛЯТЬ лишние, то нужно сравнивать и удалять явно,
                    # но для обновления прав на основе access_key обычно достаточно переопределять.
                    await discord_object.edit(overwrites=final_overwrites_map[object_id])
                    logger.debug(f"✅ Права для '{discord_object.name}' (ID: {object_id}) успешно обновлены.")
                except discord.Forbidden:
                    logger.error(
                        f"❌ У бота нет прав для обновления прав '{discord_object.name}' (ID: {object_id}). "
                        f"Проверьте разрешения бота на сервере. "
                        f"Причина: Отсутствует разрешение 'Manage Permissions' или другие необходимые права."
                    )
                except Exception as e:
                    logger.error(f"❌ Неизвестная ошибка при обновлении прав для '{discord_object.name}' (ID: {object_id}): {e}", exc_info=True)
            else:
                logger.debug(f"Нет сгенерированных прав для '{discord_object.name}' (ID: {object_id}). Пропускаем обновление.")

        logger.info(f"🎉 Обновление доступа для сервера '{guild.name}' завершено!")

    except Exception as e:
        logger.critical(f"🔥 Критическая ошибка в процессе обновления доступа для сервера '{guild.name}' ({guild.id}): {e}", exc_info=True)
        # Дополнительная обработка критической ошибки, например, уведомление администратора