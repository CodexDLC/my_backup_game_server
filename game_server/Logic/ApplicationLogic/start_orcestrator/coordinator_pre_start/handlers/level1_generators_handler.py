from typing import Optional, List, Dict, Any

from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.data_processing.creature_type_data_orchestrator import CreatureTypeDataOrchestrator
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.template_generator_character.character_template_planner import CharacterTemplatePlanner
from .base_step_handler import IPreStartStepHandler
# 👇 ИЗМЕНЕНИЕ: Импортируем единый конфиг
from game_server.config.provider import config
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорты классов планировщиков для типизации
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.template_generator_item.item_template_planner import ItemTemplatePlanner

# ДОБАВЛЕНО: Импорт оркестратора типов существ для типизации
# from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.data_processing.creature_type_data_orchestrator import CreatureTypeDataOrchestrator # Уже импортирован выше

# ДОБАВЛЕНО: Импорт ArqRedis для типизации
from arq import ArqRedis

# ДОБАВЛЕНО: Импорт PlayableRaceData DTO
from game_server.common_contracts.start_orcestrator.dtos import PlayableRaceData #


class RunLevel1GeneratorsHandler(IPreStartStepHandler):
    """ Шаг 4: Запуск планировщиков шаблонов 1 уровня (предметы и персонажи). """
    async def execute(self) -> bool:
        self.logger.debug("⚙️ Шаг 4: Запуск планировщиков шаблонов 1 уровня...")
        item_tasks_count = 0
        character_tasks_count = 0
        item_tasks_error_count = 0
        character_tasks_error_count = 0

        try:
            # --- Получаем все нужные зависимости (с точной типизацией) ---
            item_planner: ItemTemplatePlanner = self.dependencies['item_template_planner']
            character_planner: CharacterTemplatePlanner = self.dependencies['character_template_planner']
            creature_orchestrator: Optional[CreatureTypeDataOrchestrator] = self.dependencies.get('creature_type_orchestrator')
            arq_redis_client: ArqRedis = self.dependencies['arq_redis_client']
            
            # --- Генерация Предметов ---
            self.logger.info("➡️ Запуск планировщика для шаблонов ПРЕДМЕТОВ...")
            item_tasks = await item_planner.check_and_prepare_generation_tasks() # Этот метод возвращает List[Dict[str, Any]]
            
            if item_tasks:
                self.logger.info(f"Планировщик предметов подготовил {len(item_tasks)} батчей задач. Начинаем постановку в очередь ARQ...")
                for task_entry in item_tasks:
                    batch_id = task_entry.get("batch_id")
                    if batch_id:
                        try:
                            await arq_redis_client.enqueue_job(config.constants.arq.ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH, batch_id=batch_id)
                            item_tasks_count += 1
                        except Exception as arq_e:
                            item_tasks_error_count += 1
                            self.logger.error(f"❌ Ошибка постановки задачи на генерацию предмета (batch_id='{batch_id}') в очередь ARQ: {arq_e}", exc_info=True)
                    else:
                        item_tasks_error_count += 1
                        self.logger.error(f"❌ Пропуск задачи на генерацию предмета: отсутствует batch_id в записи задачи {task_entry}.")
                
                if item_tasks_count > 0:
                    self.logger.info(f"✅ Поставлено {item_tasks_count} задач на генерацию предметов в очередь ARQ. Ошибок: {item_tasks_error_count}.")
                elif item_tasks_error_count > 0:
                    self.logger.error(f"❌ Не удалось поставить ни одной задачи на генерацию предметов. Ошибок: {item_tasks_error_count}.")
                
            else:
                self.logger.info("Планировщик предметов не нашел задач для генерации.")

            # --- Генерация Персонажей ---
            self.logger.info("➡️ Запуск планировщика для шаблонов ПЕРСОНАЖЕЙ...")
            if not creature_orchestrator:
                self.logger.critical("🚨 Оркестратор данных для персонажей не был передан из предыдущего шага. Планирование персонажей невозможно.")
                raise RuntimeError("Creature orchestrator missing for character planning.")
            
            # ИЗМЕНЕНО: creature_orchestrator.get_playable_race_list() теперь возвращает List[PlayableRaceData]
            playable_races_list: List[PlayableRaceData] = creature_orchestrator.get_playable_race_list() #
            
            if not playable_races_list:
                self.logger.warning("⚠️ Список игровых рас пуст. Планирование персонажей пропускается.")
            else:
                character_tasks = await character_planner.pre_process(
                    playable_races_data=playable_races_list, #
                    desired_gender_ratio=config.settings.prestart.DEFAULT_CHARACTER_GENDER_RATIO
                )
                if character_tasks:
                    self.logger.info(f"Планировщик персонажей подготовил {len(character_tasks)} батчей задач. Начинаем постановку в очередь ARQ...")
                    for task_entry in character_tasks:
                        batch_id = task_entry.get("batch_id")
                        if batch_id:
                            try:
                                await arq_redis_client.enqueue_job(config.constants.arq.ARQ_TASK_GENERATE_CHARACTER_BATCH, batch_id=batch_id)
                                character_tasks_count += 1
                            except Exception as arq_e:
                                character_tasks_error_count += 1
                                self.logger.error(f"❌ Ошибка постановки задачи на генерацию персонажа (batch_id='{batch_id}') в очередь ARQ: {arq_e}", exc_info=True)
                        else:
                            character_tasks_error_count += 1
                            self.logger.error(f"❌ Пропуск задачи на генерацию персонажа: отсутствует batch_id в записи задачи {task_entry}.")
                    
                    if character_tasks_count > 0:
                        self.logger.info(f"✅ Поставлено {character_tasks_count} задач на генерацию персонажей в очередь ARQ. Ошибок: {character_tasks_error_count}.")
                    elif character_tasks_error_count > 0:
                        self.logger.error(f"❌ Не удалось поставить ни одной задачи на генерацию персонажей. Ошибок: {character_tasks_error_count}.")
                else:
                    self.logger.info("Планировщик персонажей не нашел задач для генерации.")
            
            self.logger.info("✅ Шаг 4: Планировщики шаблонов 1 уровня завершили свою работу.")
            return True
        except RuntimeError as e:
            self.logger.critical(f"🚨 Шаг 4: Критическая ошибка в планировщиках 1 уровня: {e}", exc_info=True)
            return False
        except Exception as e:
            self.logger.critical(f"🚨 Шаг 4: Непредвиденная критическая ошибка при запуске планировщиков 1 уровня: {e}", exc_info=True)
            return False