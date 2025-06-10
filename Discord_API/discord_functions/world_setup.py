
import asyncio
from typing import Any, Dict, List
import discord
from Discord_API.config.logging.logging_setup import logger
from Discord_API.discord_functions.utils.discord_api_helpers import execute_discord_api_call, is_name_conflict_error
from Discord_API.discord_functions.utils.world_setup_gogs.setup_roles_utils import fetch_actual_guild_roles, save_roles_bindings_to_db, send_and_delete_temp_message
from Discord_API.discord_functions.utils.world_setup_gogs.wolrd_setup_utils import (    
 
    create_category_if_not_exists, 
    create_text_channel_if_not_exists,

)
from Discord_API.discord_settings import  ( # <--- Убедитесь, что путь правильный
    MAX_RETRIES_PER_ROLE,
    INITIAL_SHORT_PAUSE,
    RATE_LIMIT_PAUSE,
    CREATION_TIMEOUT,
    MAX_RETRY_SLEEP
)


async def _process_discord_categories_creation(
    guild: discord.Guild, 
    category_bindings_to_process: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Создает недостающие Discord-категории и обновляет их ID в привязках,
    а также пересоздает категории, которые были удалены из Discord, но остались в БД.
    """
    logger.info("Начало обработки создания/пересоздания Discord категорий.")
    updated_bindings = []
    
    for binding in category_bindings_to_process:
        discord_category_id = binding.get("category_id")
        category_name = binding.get("category_name") # Убедитесь, что category_name тут есть

        if not category_name:
            logger.warning(f"Пропущена привязка категории без 'category_name': {binding}")
            continue # Пропускаем, если нет имени категории

        discord_category = None
        
        # Шаг 1: Проверяем, есть ли привязка в БД и существует ли объект в Discord
        if discord_category_id: 
            try:
                # Пытаемся получить объект категории из Discord по ID
                discord_category = guild.get_channel(int(discord_category_id))
            except ValueError: # Если discord_category_id почему-то не число
                logger.error(f"Некорректный Discord category_id '{discord_category_id}' для категории '{category_name}'. Будет пересоздана.")
                discord_category = None # Принудительно ставим None, чтобы пересоздать
            
            if discord_category is None:
                # Если объект не найден в Discord, но ID был (т.е. он был удален),
                # мы логируем это и помечаем как "нужно создать".
                logger.warning(f"Категория Discord '{category_name}' (ID: {discord_category_id}) не найдена в гильдии. Помечаем для пересоздания.")
                binding["category_id"] = None # Сбрасываем ID, чтобы ветка создания сработала
        
        # Шаг 2: Создаем категорию, если она еще не существует или была помечена для пересоздания
        if discord_category is None: # Это условие верно, если category_id был None ИЛИ если объект не найден в Discord
            logger.info(f"Создание новой Discord категории: {category_name}")
            try:
                # Проверяем, существует ли категория с таким именем, чтобы избежать дубликатов
                existing_discord_category_by_name = discord.utils.get(guild.categories, name=category_name)
                if existing_discord_category_by_name:
                    logger.warning(f"Категория '{category_name}' уже существует в Discord. Используем существующую.")
                    new_category = existing_discord_category_by_name
                else:
                    new_category = await guild.create_category(category_name)
                
                binding["category_id"] = str(new_category.id)
                logger.info(f"Категория '{category_name}' успешно создана/найдена с ID: {new_category.id}")

            except discord.Forbidden:
                logger.error(f"Боту не хватает прав для создания категории '{category_name}'. Пропустим.", exc_info=True)
                # Если ошибка прав, не устанавливаем ID, чтобы привязка не сохранялась с некорректным ID
                binding["category_id"] = None
            except discord.HTTPException as e:
                logger.error(f"Ошибка API Discord при создании категории '{category_name}' (статус: {e.status}): {e.text}", exc_info=True)
                binding["category_id"] = None
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при создании категории '{category_name}': {e}", exc_info=True)
                binding["category_id"] = None
        else:
            logger.debug(f"Категория Discord '{category_name}' (ID: {discord_category.id}) уже существует и актуальна.")
            # Если категория существует, убедимся, что ID в binding корректен
            binding["category_id"] = str(discord_category.id)

        updated_bindings.append(binding)

    logger.info("Завершено создание/пересоздание Discord категорий.")
    return [b for b in updated_bindings if b.get("category_id")] # Возвращаем только те, для которых удалось получить ID



# ... (Предыдущие импорты и вспомогательные функции) ...

async def _process_discord_channels_creation(
    guild: discord.Guild,
    channel_bindings_to_process: List[Dict[str, Any]],
    current_discord_category_ids_map: Dict[str, str] # Карта с ID всех категорий
) -> List[Dict[str, Any]]:
    """
    Создает недостающие текстовые каналы Discord и обновляет их ID в привязках,
    а также пересоздает каналы, которые были удалены из Discord, но остались в БД.
    """
    logger.info("Начало обработки создания/пересоздания Discord каналов.")
    updated_bindings = []

    for binding in channel_bindings_to_process:
        discord_channel_id = binding.get("channel_id")
        channel_name = binding.get("channel_name") # Убедитесь, что channel_name тут есть
        parent_access_key = binding.get("parent_access_key") # Access Key родительской категории

        if not channel_name:
            logger.warning(f"Пропущена привязка канала без 'channel_name': {binding}")
            continue

        # Получаем Discord ID родительской категории
        parent_discord_category_id = current_discord_category_ids_map.get(parent_access_key)
        if not parent_discord_category_id:
            logger.warning(f"Не найден Discord ID для родительской категории '{parent_access_key}' канала '{channel_name}'. Канал не будет создан.")
            continue # Пропускаем канал, если нет родительской категории

        parent_category_obj = guild.get_channel(int(parent_discord_category_id))
        if not parent_category_obj:
            logger.warning(f"Родительская категория с ID {parent_discord_category_id} для канала '{channel_name}' не найдена в Discord. Канал не будет создан.")
            continue # Пропускаем, если родительской категории нет в Discord

        discord_channel = None

        # Шаг 1: Проверяем, есть ли привязка в БД и существует ли объект в Discord
        if discord_channel_id:
            try:
                # Пытаемся получить объект канала из Discord по ID
                discord_channel = guild.get_channel(int(discord_channel_id))
            except ValueError: # Если discord_channel_id почему-то не число
                logger.error(f"Некорректный Discord channel_id '{discord_channel_id}' для канала '{channel_name}'. Будет пересоздан.")
                discord_channel = None # Принудительно ставим None, чтобы пересоздать

            if discord_channel is None:
                # Если объект не найден в Discord, но ID был (т.е. он был удален),
                # мы логируем это и помечаем как "нужно создать".
                logger.warning(f"Канал Discord '{channel_name}' (ID: {discord_channel_id}) не найден в гильдии. Помечаем для пересоздания.")
                binding["channel_id"] = None # Сбрасываем ID, чтобы ветка создания сработала

        # Шаг 2: Создаем канал, если он еще не существует или был помечен для пересоздания
        if discord_channel is None:
            logger.info(f"Создание нового Discord канала: {channel_name} в категории '{parent_category_obj.name}'")
            try:
                # Проверяем, существует ли канал с таким именем в данной категории
                existing_discord_channel_by_name = discord.utils.get(parent_category_obj.channels, name=channel_name)
                if existing_discord_channel_by_name:
                    logger.warning(f"Канал '{channel_name}' уже существует в категории '{parent_category_obj.name}'. Используем существующий.")
                    new_channel = existing_discord_channel_by_name
                else:
                    new_channel = await guild.create_text_channel(channel_name, category=parent_category_obj)
                
                binding["channel_id"] = str(new_channel.id)
                logger.info(f"Канал '{channel_name}' успешно создан/найден с ID: {new_channel.id}")

            except discord.Forbidden:
                logger.error(f"Боту не хватает прав для создания канала '{channel_name}' в категории '{parent_category_obj.name}'. Пропустим.", exc_info=True)
                binding["channel_id"] = None
            except discord.HTTPException as e:
                logger.error(f"Ошибка API Discord при создании канала '{channel_name}' (статус: {e.status}): {e.text}", exc_info=True)
                binding["channel_id"] = None
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при создании канала '{channel_name}': {e}", exc_info=True)
                binding["channel_id"] = None
        else:
            logger.debug(f"Канал Discord '{channel_name}' (ID: {discord_channel.id}) уже существует и актуален.")
            binding["channel_id"] = str(discord_channel.id)

        updated_bindings.append(binding)

    logger.info("Завершено создание/пересоздание Discord каналов.")
    return [b for b in updated_bindings if b.get("channel_id")] # Возвращаем только те, для которых удалось получить ID





async def create_discord_roles(guild: discord.Guild, roles_data_from_db: List[Dict]) -> List[Dict]:
    """
    Создаёт или обновляет роли в Discord на основе данных из БД в два этапа:
    1. Находит и связывает существующие роли.
    2. Создаёт недостающие роли.
    Возвращает окончательный список привязок ролей (включая ID Discord) для записи в БД.
    """
    logger.info(f"DEBUG: Начало функции create_discord_roles для гильдии {guild.id}")

    final_roles_bindings_to_save = [] # Окончательный список для сохранения в БД
    roles_to_create_later = []       # Список ролей, которые не были найдены и нуждаются в создании
    total_roles_to_process = len(roles_data_from_db)

    if total_roles_to_process == 0:
        logger.info(f"🚫 Нет ролей для обработки в гильдии '{guild.name}'.")
        return []

    try:
        await send_and_delete_temp_message(
            guild.system_channel,
            f"🚀 Начинаем синхронизацию {total_roles_to_process} ролей для гильдии **{guild.name}**."
        )

        logger.info(f"🚀 Начинаем синхронизацию {total_roles_to_process} ролей в Discord для гильдии '{guild.name}' ({guild.id}).")

        current_discord_roles = await fetch_actual_guild_roles(guild)
        if not current_discord_roles:
            logger.error(f"❌ Не удалось получить актуальный список ролей для гильдии '{guild.name}'. Выходим.")
            return []

        discord_roles_by_name = {role.name: role for role in current_discord_roles}
        discord_roles_by_id = {role.id: role for role in current_discord_roles}

        # --- ФАЗА 1: Поиск и привязка существующих ролей ---
        logger.info("--- ФАЗА 1: Поиск и привязка существующих ролей ---")
        found_and_bound_count = 0
        for index, role_data in enumerate(roles_data_from_db):
            role_name = role_data.get("role_name")
            access_code = role_data.get("access_code")
            db_role_id = role_data.get("role_id")
            permissions_value = role_data.get("permissions", 0)
            permissions = discord.Permissions(permissions_value)

            if not role_name:
                logger.warning(f"⚠️ Пропущена запись роли из-за отсутствия 'role_name': {role_data}")
                continue

            processed_successfully_in_phase_1 = False
            discord_role_obj = None

            # 1. Поиск по существующему Discord ID (если есть в БД)
            if db_role_id:
                discord_role_obj = discord_roles_by_id.get(db_role_id)
                if discord_role_obj and discord_role_obj.name == role_name:
                    logger.info(f"ℹ️ Роль '{role_name}' (ID: {db_role_id}) найдена по ID. Привязываем.")
                    processed_successfully_in_phase_1 = True
                elif discord_role_obj:
                    logger.warning(f"⚠️ Роль '{role_name}' (ID: {db_role_id}) найдена по ID, но имя изменилось на '{discord_role_obj.name}'. Привязываем.")
                    processed_successfully_in_phase_1 = True
            
            # 2. Если не найдена по ID, или ID не было, ищем по имени
            if not processed_successfully_in_phase_1:
                discord_role_obj = discord_roles_by_name.get(role_name)
                if discord_role_obj:
                    logger.info(f"ℹ️ Роль '{role_name}' найдена по имени (ID: {discord_role_obj.id}). Привязываем.")
                    processed_successfully_in_phase_1 = True
            
            if processed_successfully_in_phase_1:
                final_roles_bindings_to_save.append({
                    "guild_id": guild.id,
                    "access_code": access_code,
                    "role_name": role_name,
                    "role_id": discord_role_obj.id, # Используем актуальный ID из Discord
                    "permissions": permissions_value
                })
                found_and_bound_count += 1
            else:
                # Если роль не была найдена в Discord ни по ID, ни по имени,
                # значит, её нужно будет создать на следующем этапе.
                roles_to_create_later.append(role_data)
                logger.info(f"⏳ Роль '{role_name}' не найдена в Discord. Отложена для создания.")

        logger.info(f"--- ФАЗА 1 ЗАВЕРШЕНА: Найдено и привязано {found_and_bound_count} ролей. {len(roles_to_create_later)} ролей нуждаются в создании. ---")

        # --- Сохраняем результаты Фазы 1 в БД ---
        await save_roles_bindings_to_db(guild.id, final_roles_bindings_to_save)
        logger.info(f"✅ Результаты Фазы 1 успешно сохранены в БД.")

        # Если не осталось ролей для создания, то завершаем
        if not roles_to_create_later:
            logger.info("🚫 Все роли найдены или привязаны. Нет ролей для создания. Синхронизация завершена.")
            await send_and_delete_temp_message(
                guild.system_channel,
                f"✅ Завершено синхронизацию ролей. **{len(final_roles_bindings_to_save)}** ролей обработано."
            )
            return final_roles_bindings_to_save


        # --- ФАЗА 2: Создание недостающих ролей ---
        logger.info("--- ФАЗА 2: Создание недостающих ролей ---")
        current_inter_request_pause = INITIAL_SHORT_PAUSE # Пауза сбрасывается для новой фазы
        created_roles_count = 0
        
        # Новый флаг для отслеживания, была ли проблема в Фазе 2, требующая прерывания
        problem_encountered_in_phase_2 = False 

        for index, role_data in enumerate(roles_to_create_later):
            role_name = role_data.get("role_name")
            access_code = role_data.get("access_code")
            permissions_value = role_data.get("permissions", 0)
            permissions = discord.Permissions(permissions_value)

            encountered_problem_in_api_call_for_current_role = False 

            logger.info(f"⏳ ({index + 1}/{len(roles_to_create_later)}) Создаём новую роль: '{role_name}' (Access Code: {access_code})...")
            try:
                new_role, problem_flag_from_api_call = await execute_discord_api_call( 
                    lambda: guild.create_role(name=role_name, permissions=permissions, reason=f"Синхронизация роли для мира: {role_name}"),
                    description=f"создание роли '{role_name}'",
                    timeout=CREATION_TIMEOUT,
                    retries=MAX_RETRIES_PER_ROLE
                )
                
                if problem_flag_from_api_call:
                    encountered_problem_in_api_call_for_current_role = True
                    current_inter_request_pause = MAX_RETRY_SLEEP
                    logger.info(f"⚠️ Рейт-лимит/таймаут обнаружен в execute_discord_api_call. Межзапросная пауза установлена на {current_inter_request_pause} сек.")
                
                logger.info(f"✅ Создана роль: **{new_role.name}** (ID: {new_role.id}).")
                final_roles_bindings_to_save.append({ # Добавляем в общий список
                    "guild_id": guild.id,
                    "access_code": access_code,
                    "role_name": role_name,
                    "role_id": new_role.id,
                    "permissions": permissions_value
                })
                created_roles_count += 1

            except discord.Forbidden:
                logger.error(f"❌ ОШИБКА: Недостаточно прав для создания роли '{role_name}' в гильдии '{guild.name}'. Проверьте разрешения бота! Пропускаем эту роль.", exc_info=True)
                encountered_problem_in_api_call_for_current_role = True
                current_inter_request_pause = MAX_RETRY_SLEEP
                problem_encountered_in_phase_2 = True # ❗ Обнаружена проблема, которая должна прервать фазу
            except discord.HTTPException as e:
                if is_name_conflict_error(e):
                    logger.warning(f"⚠️ Роль '{role_name}' уже существует в Discord (конфликт имени) - конфликт после проверки в Фазе 1. Пытаемся привязать.")
                    rechecked_role = discord_roles_by_name.get(role_name)
                    if rechecked_role:
                        final_roles_bindings_to_save.append({
                            "guild_id": guild.id,
                            "access_code": access_code,
                            "role_name": role_name,
                            "role_id": rechecked_role.id,
                            "permissions": permissions_value
                        })
                        logger.info(f"ℹ️ Роль '{role_name}' добавлена по существующему ID: {rechecked_role.id}.")
                        created_roles_count += 1 # Считаем как успешно обработанную
                    else:
                        logger.error(f"❌ Конфликт имени роли '{role_name}', но роль не найдена после перепроверки в Фазе 2. Продолжаем.", exc_info=True)
                        encountered_problem_in_api_call_for_current_role = True
                        current_inter_request_pause = MAX_RETRY_SLEEP
                        problem_encountered_in_phase_2 = True # ❗ Обнаружена проблема
                else:
                    logger.error(f"❌ Не удалось создать роль '{role_name}' из-за HTTP ошибки: {e}. Пропускаем.", exc_info=True)
                    encountered_problem_in_api_call_for_current_role = True
                    current_inter_request_pause = MAX_RETRY_SLEEP
                    problem_encountered_in_phase_2 = True # ❗ Обнаружена проблема
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Не удалось создать роль '{role_name}' после всех попыток из-за таймаута Discord API (60с). Пропускаем.", exc_info=True)
                encountered_problem_in_api_call_for_current_role = True
                current_inter_request_pause = MAX_RETRY_SLEEP
                problem_encountered_in_phase_2 = True # ❗ Обнаружена проблема
            except Exception as e:
                logger.error(f"❌ Не удалось создать роль '{role_name}' после всех попыток из-за непредвиденной ошибки: {e}. Пропускаем.", exc_info=True)
                encountered_problem_in_api_call_for_current_role = True
                current_inter_request_pause = MAX_RETRY_SLEEP
                problem_encountered_in_phase_2 = True # ❗ Обнаружена проблема

            # --- Динамическая пауза для Фазы 2 ---
            # Пауза происходит только если это не последняя роль и нет критической проблемы
            if not problem_encountered_in_phase_2 and index < len(roles_to_create_later) - 1:
                logger.info(f"➡️ Завершили обработку роли '{role_name}'. Ждем {current_inter_request_pause} сек. перед следующей...")
                await asyncio.sleep(current_inter_request_pause)
                logger.info(f"✅ Пауза завершена. Готовы к следующей роли.")
                
                # Если текущая операция прошла без проблем с рейт-лимитами/таймаутами
                if not encountered_problem_in_api_call_for_current_role:
                     current_inter_request_pause = INITIAL_SHORT_PAUSE
                     logger.info(f"🚀 Проблем (таймаутов/рейт-лимитов) не обнаружено. Пауза сброшена до {current_inter_request_pause} сек.")
            
            # ❗ НОВОЕ: Если в Фазе 2 произошла серьезная проблема, прерываем цикл создания
            if problem_encountered_in_phase_2:
                logger.error(f"❌ Прерываем создание ролей в Фазе 2 из-за критической ошибки для роли '{role_name}'.")
                break # Выход из цикла for

        logger.info(f"--- ФАЗА 2 ЗАВЕРШЕНА: Создано {created_roles_count} новых ролей. ---")
        
        # --- Сохраняем окончательные результаты (Фаза 1 + Фаза 2) в БД ---
        await save_roles_bindings_to_db(guild.id, final_roles_bindings_to_save)
        logger.info(f"✅ Окончательные результаты синхронизации успешно сохранены в БД.")

        # Отправляем финальное сообщение в зависимости от того, была ли проблема
        if problem_encountered_in_phase_2:
            await send_and_delete_temp_message(
                guild.system_channel,
                f"⚠️ Синхронизация ролей **завершена с проблемами**. Обработано {created_roles_count} новых ролей, но не все роли могли быть созданы. Проверьте логи."
            )
        else:
            await send_and_delete_temp_message(
                guild.system_channel,
                f"✅ Завершено синхронизацию ролей. **{len(final_roles_bindings_to_save)}** ролей обработано."
            )

        return final_roles_bindings_to_save

    except Exception as e:
        logger.critical(f"🔥 КРИТИЧЕСКАЯ ОШИБКА в create_discord_roles для гильдии '{guild.name}': {e}", exc_info=True)
        await send_and_delete_temp_message(
            guild.system_channel,
            f"❌ КРИТИЧЕСКАЯ ОШИБКА при синхронизации ролей: {e}. Пожалуйста, проверьте логи."
        )
        return []