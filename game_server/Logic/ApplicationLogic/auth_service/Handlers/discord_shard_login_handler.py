# game_server/Logic/ApplicationLogic/auth_service/Handlers/discord_shard_login_handler.py

from typing import Dict, Any

from game_server.common_contracts.shared_models.api_contracts import ErrorDetail

from .i_auth_handler import IAuthHandler

# Импортируем ваш глобальный логгер
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые стандартизированные DTO
from game_server.common_contracts.dtos.auth_dtos import DiscordShardLoginCommandDTO, SessionResultData, SessionResultDTO, HubRoutingResultDTO # Теперь ShardLoginResult это HubRoutingResultDTO



class DiscordShardLoginHandler(IAuthHandler):
    """
    Обработчик для Роута №2: создание сессии для пользователя, находящегося на шарде.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        self.logger = logger
        try:
            self.repo_manager = dependencies['repository_manager']
            self.session_manager = dependencies['session_manager'] # Менеджер сессий, который работает с Redis
            self.identifiers_service = dependencies['identifiers_service']
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise RuntimeError(f"Missing mandatory dependency in {self.__class__.__name__}: {e}")

    # 🔥 ИЗМЕНЕНИЕ: dto теперь DiscordShardLoginCommandDTO, возвращает HubRoutingResultDTO
    async def process(self, dto: DiscordShardLoginCommandDTO) -> HubRoutingResultDTO:
        self.logger.info(f"Начало процесса создания сессии для discord_id: {dto.discord_user_id} (Correlation ID: {dto.correlation_id})")

        try:
            # Шаг А: Поиск аккаунта
            account_id = await self.identifiers_service.get_account_id_by_linked_platform(
                platform_name='discord',
                platform_id=dto.discord_user_id
            )
            if not account_id:
                msg = f"Попытка входа с шарда для несуществующего аккаунта: {dto.discord_user_id}"
                self.logger.warning(msg)
                # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=False и ErrorDetail
                return HubRoutingResultDTO(
                    correlation_id=dto.correlation_id,
                    trace_id=dto.trace_id,
                    span_id=dto.span_id,
                    success=False,
                    message=msg,
                    error=ErrorDetail(code="ACCOUNT_NOT_FOUND", message=msg)
                )

            # Шаг Б: Проверка "прописки" (валидация шарда)
            game_data = await self.repo_manager.account_game_data.get_by_account_id(account_id)

            # Шаг В: Условная логика для "бездомного" игрока
            if not game_data or not game_data.shard_id:
                msg = f"Игрок {account_id} не привязан к шарду. Требуется вход через Хаб."
                self.logger.warning(msg)
                self.logger.info(f"КОМАНДА БОТУ: 'notify_re_login_via_hub' для discord_id {dto.discord_user_id} (Correlation ID: {dto.correlation_id})")
                # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=False и ErrorDetail
                return HubRoutingResultDTO(
                    correlation_id=dto.correlation_id,
                    trace_id=dto.trace_id,
                    span_id=dto.span_id,
                    success=False,
                    message=msg,
                    error=ErrorDetail(code="RE_HUB_LOGIN_REQUIRED", message=msg)
                )

            # Шаг Г: Создание сессии и токена
            self.logger.info(f"Игрок {account_id} успешно прошел проверку шарда. Создание сессии... (Correlation ID: {dto.correlation_id})")
            auth_token = await self.session_manager.create_player_session(player_id=str(account_id))

            # Шаг Д: Успешный ответ
            # 🔥 ИЗМЕНЕНИЕ: Возвращаем SessionResultDTO, который теперь сам BaseResultDTO
            return SessionResultDTO(
                correlation_id=dto.correlation_id,
                trace_id=dto.trace_id,
                span_id=dto.span_id,
                success=True,
                message="Сессия успешно создана.",
                data=SessionResultData(auth_token=auth_token) # Вкладываем данные в поле 'data'
            )

        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при создании сессии для discord_id {dto.discord_user_id} (Correlation ID: {dto.correlation_id})")
            # 🔥 ИЗМЕНЕНИЕ: Возвращаем HubRoutingResultDTO с success=False и ErrorDetail
            return HubRoutingResultDTO(
                correlation_id=dto.correlation_id,
                trace_id=dto.trace_id,
                span_id=dto.span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {str(e)}",
                error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(e))
            )