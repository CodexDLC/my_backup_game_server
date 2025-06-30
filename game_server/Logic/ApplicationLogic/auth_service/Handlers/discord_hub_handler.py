# game_server/Logic/ApplicationLogic/auth_service/Handlers/discord_hub_handler.py

import logging
from typing import Dict, Any, Union

from game_server.common_contracts.shared_models.api_contracts import ErrorDetail


from .i_auth_handler import IAuthHandler

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые стандартизированные DTO
from game_server.common_contracts.dtos.auth_dtos import HubRoutingCommandDTO, HubRoutingResultDTO, HubRoutingResultData # HubRoutingResult теперь HubRoutingResultDTO



class DiscordHubHandler(IAuthHandler):
    """
    Обработчик для Роута №1: находит/создает аккаунт и определяет шард для маршрутизации.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        # 🔥 ИЗМЕНЕНИЕ: Используем глобальный логгер, если он доступен в зависимостях
        self.logger = dependencies.get('logger', logging.getLogger(self.__class__.__name__))
        try:
            # Извлекаем все нужные зависимости
            self.repo_manager = dependencies['repository_manager']
            self.identifiers_service = dependencies['identifiers_service']
            self.account_creator = dependencies['account_creator']
            self.shard_manager = dependencies['shard_manager']
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise RuntimeError(f"Missing mandatory dependency in {self.__class__.__name__}: {e}")

    # 🔥 ИЗМЕНЕНИЕ: dto теперь HubRoutingCommandDTO, возвращает HubRoutingResultDTO
    async def process(self, dto: HubRoutingCommandDTO) -> HubRoutingResultDTO:
        self.logger.info(f"Начало процесса маршрутизации для discord_id: {dto.discord_user_id} (Correlation ID: {dto.correlation_id})")

        try:
            # Шаг 1: Поиск существующего аккаунта
            account_id = await self.identifiers_service.get_account_id_by_linked_platform(
                platform_name='discord',
                platform_id=dto.discord_user_id
            )

            # Шаг 2: Создание нового аккаунта (если необходимо)
            if not account_id:
                self.logger.info(f"Аккаунт для discord_id {dto.discord_user_id} не найден. Создание нового. (Correlation ID: {dto.correlation_id})")
                # 🔥 ПРИМЕЧАНИЕ: Предполагается, что create_new_discord_account теперь принимает HubRoutingCommandDTO
                # и возвращает dict с 'account_id', или AccountCreationResultDTO
                creation_result = await self.account_creator.create_new_discord_account(dto)
                account_id = creation_result['account_id']
            else:
                self.logger.info(f"Найден существующий аккаунт: {account_id} (Correlation ID: {dto.correlation_id})")

            # Шаг 3: Определение и сохранение Шарда
            shard_id = await self.shard_manager.get_or_assign_shard_for_account(
                account_id=account_id,
                preferred_shard_id=dto.guild_id, # Передаем guild_id хаба как предпочтительный
                correlation_id=dto.correlation_id, # 🔥 ПЕРЕДАЕМ CORRELATION_ID
                trace_id=dto.trace_id,             # 🔥 ПЕРЕДАЕМ TRACE_ID
                span_id=dto.span_id                # 🔥 ПЕРЕДАЕМ SPAN_ID
            )

            if not shard_id:
                msg = f"Не удалось определить шард для игрока {account_id} (Correlation ID: {dto.correlation_id})."
                self.logger.error(msg)
                # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=False и ErrorDetail
                return HubRoutingResultDTO(
                    correlation_id=dto.correlation_id,
                    trace_id=dto.trace_id,
                    span_id=dto.span_id,
                    success=False,
                    message=msg,
                    error=ErrorDetail(code="SHARD_ASSIGNMENT_FAILED", message=msg)
                )

            self.logger.info(f"Игроку {account_id} назначен шард: {shard_id} (Correlation ID: {dto.correlation_id})")

            # Шаг 4: Формирование успешного ответа
            # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=True и HubRoutingResultData
            return HubRoutingResultDTO(
                correlation_id=dto.correlation_id,
                trace_id=dto.trace_id,
                span_id=dto.span_id,
                success=True,
                message="Маршрутизация успешно выполнена.",
                data=HubRoutingResultData(account_id=account_id, shard_id=shard_id) # Вкладываем данные в поле 'data'
            )

        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при маршрутизации для discord_id {dto.discord_user_id} (Correlation ID: {dto.correlation_id})")
            # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=False и ErrorDetail
            return HubRoutingResultDTO(
                correlation_id=dto.correlation_id,
                trace_id=dto.trace_id,
                span_id=dto.span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {str(e)}",
                error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(e))
            )