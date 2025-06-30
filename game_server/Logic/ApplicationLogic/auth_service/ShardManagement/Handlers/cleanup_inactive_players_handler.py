# game_server\Logic\ApplicationLogic\auth_service\ShardManagement\Handlers\cleanup_inactive_players_handler.py

import logging
import datetime
from typing import Dict, Any
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError

from .i_shard_management_handler import IShardManagementHandler
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager

# --- КОНСТАНТА ДЛЯ ПОРОГА НЕАКТИВНОСТИ ---
# Позже может быть вынесена в файл с настройками.
INACTIVITY_THRESHOLD = datetime.timedelta(hours=24)

class CleanupInactivePlayersHandler(IShardManagementHandler):
    """
    Обработчик, отвечающий за очистку "прописки" у неактивных игроков для освобождения слотов.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.shard_count_manager: ShardCountCacheManager = self.dependencies['shard_count_manager']
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    async def process(self) -> Dict[str, int]:
        """
        Выполняет полный цикл очистки неактивных игроков.
        Возвращает словарь-отчет вида {'shard_id': freed_slots_count}.
        """
        self.logger.info("Запуск процесса очистки неактивных игроков...")
        
        try:
            # 1. Определяем временную отметку, раньше которой игроки считаются неактивными
            threshold_date = datetime.datetime.now(datetime.timezone.utc) - INACTIVITY_THRESHOLD
            
            # 2. Ищем кандидатов на удаление через репозиторий
            # Метод должен вернуть список объектов/словарей, содержащих как минимум account_id и shard_id
            inactive_players = await self.repo_manager.account_game_data.find_inactive_players_on_shards(
                last_login_field_name='last_login_game',
                threshold_date=threshold_date
            )

            if not inactive_players:
                self.logger.info("Неактивные игроки для очистки не найдены.")
                return {}

            # 3. Группируем игроков по шардам и собираем их ID
            players_by_shard = defaultdict(list)
            player_ids_to_clear = []
            for player in inactive_players:
                players_by_shard[player.shard_id].append(player.account_id)
                player_ids_to_clear.append(player.account_id)

            self.logger.info(f"Найдено {len(player_ids_to_clear)} неактивных игроков на {len(players_by_shard)} шардах.")

            # 4. Очищаем shard_id в БД для всех найденных игроков
            await self.repo_manager.account_game_data.clear_shard_id_for_players(player_ids_to_clear)

            # 5. Декрементируем счетчики в кэше Redis
            report = {}
            for shard_id, players in players_by_shard.items():
                count = len(players)
                await self.shard_count_manager.decrement_shard_player_count(shard_id, count)
                report[shard_id] = count
                self.logger.info(f"Освобождено {count} слотов на шарде {shard_id}.")

            self.logger.info("Процесс очистки неактивных игроков успешно завершен.")
            return report

        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка базы данных во время очистки игроков: {e}")
            return {}
        except Exception as e:
            # Здесь может быть ошибка Redis или другая
            self.logger.exception(f"Непредвиденная ошибка во время очистки игроков: {e}")
            return {}