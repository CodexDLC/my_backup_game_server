# game_server/api_fast/rest_routers/discord/discord_roles_mapping.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging
# import uuid # Больше не нужен, т.к. world_id удален и не парсится здесь

# Импорты Pydantic моделей для запросов и ответов (из вашего api_fast)
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response
from game_server.api_fast.api_models.discord_api import (
    StateEntityDiscordCreateUpdateRequest, # API-модель для отдельной роли (входящая) - оставим, если API-контракт не меняется, но не используем
    StateEntityDiscordAPIResponse, # API-модель для ответа об одной роли (исходящая)
    StateEntityDiscordBatchCreateUpdateRequest, # API-модель для пакетного создания/обновления (входящая)
    StateEntityDiscordBatchDeleteRequest, # API-модель для пакетного удаления запроса (входящая)
    StateEntityDiscordBatchDeleteResponseData # API-модель для пакетного удаления ответа (исходящая)
)

# Импорт сервисного слоя (бизнес-логики) из ApplicationLogic
from game_server.Logic.ApplicationLogic.DiscordIntegration.Discord_State_Entities_logic import StateEntitiesDiscordLogic

# Импорт новых DTO-моделей из common_contracts
from common_contracts.discord_integration.discord_commands_and_events import (
    StateEntityDiscordDTO,
    StateEntityDiscordCreateUpdateCommand,
    StateEntityDiscordDeleteCommand, # Теперь только с guild_id и discord_role_id
    StateEntitiesDiscordBatchCreateCommand
)

# Импорт общих зависимостей из api_fast/dependencies.py
from api_fast.dependencies import (
    get_state_entities_discord_logic
)

# Импортируем настроенный глобальный логгер сервера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

router = APIRouter()

# --- Роут для пакетной синхронизации Discord ролей ---
@router.post(
    "/roles/sync-batch",
    response_model=APIResponse[Dict[str, Any]], # Пока оставляем Dict[str, Any] как в оригинале
    summary="Синхронизировать Discord роли (пакетно)"
)
async def sync_discord_roles_batch(
    request_data_api: StateEntityDiscordBatchCreateUpdateRequest, # Входящая API Pydantic модель
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic) # Используем централизованную зависимость
):
    logger.info(f"Получены данные в роуте sync_discord_roles_batch. Тип request_data_api: {type(request_data_api)}")
    logger.info(f"Тип request_data_api.roles: {type(request_data_api.roles)}")

    received_roles_count = len(request_data_api.roles)
    logger.debug(f"Количество ролей, полученных от FastAPI/Pydantic: {received_roles_count}")

    for i, role_item in enumerate(request_data_api.roles):
        try:
            logger.debug(f"Данные роли {i+1} (Pydantic API Model): {role_item.model_dump()}")
        except Exception as e:
            logger.error(f"Ошибка при дампе Pydantic-модели роли {i+1}: {e}", exc_info=True)
            continue

    try:
        # 1. Преобразование API-модели (StateEntityDiscordBatchCreateUpdateRequest)
        # в Internal DTO Command (StateEntitiesDiscordBatchCreateCommand)
        role_create_update_commands: List[StateEntityDiscordCreateUpdateCommand] = []
        for role_api_model in request_data_api.roles:
            # Преобразуем каждую API-модель в DTO-команду
            role_create_update_commands.append(StateEntityDiscordCreateUpdateCommand(**role_api_model.model_dump()))

        sync_command = StateEntitiesDiscordBatchCreateCommand(
            roles_batch=role_create_update_commands
        )
        logger.debug(f"Преобразованные данные для логики. Количество ролей: {len(sync_command.roles_batch)}")
        if sync_command.roles_batch:
            logger.debug(f"Пример первой преобразованной роли (DTO): {sync_command.roles_batch[0].model_dump()}")

        # 2. Вызов бизнес-логики с DTO-командой
        result_from_logic = await logic_service.create_roles_discord(sync_command)

        if result_from_logic.get("errors"):
            error_messages = [
                err.get('message', 'Неизвестная ошибка синхронизации.')
                for err in result_from_logic.get('errors', [])
            ]
            overall_error_message = "Синхронизация завершена с ошибками: " + "; ".join(error_messages)

            for err in result_from_logic.get('errors', []):
                if err.get('backend_sync') == 'Ошибка' and err.get('message') == 'Роли успешно синхронизированы.':
                    logger.error(f"❌ Обнаружено противоречивое сообщение об ошибке от логики: {err.get('message')}. Требуется исправление в логике/менеджере.")

            return create_error_response(
                code="PARTIAL_SYNC_FAILED",
                message=overall_error_message,
                data=result_from_logic
            )
        else:
            return create_success_response(data=result_from_logic, message="Роли успешно синхронизированы.")
    except ValueError as e:
        logger.warning(f"Некорректные данные для массовой вставки ролей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code="VALIDATION_ERROR", message=str(e)).model_dump()
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при синхронизации ролей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message=f"Внутренняя ошибка сервера: {e}").model_dump()
        )

# --- Обновленный роут для пакетного удаления Discord ролей ---
# Этот роут теперь будет вызывать delete_roles_batch_by_role_ids
@router.delete(
    "/roles/delete-batch",
    response_model=APIResponse[StateEntityDiscordBatchDeleteResponseData],
    summary="Удалить Discord роли (пакетно)",
    description="Удаляет записи о ролях Discord из базы данных по списку ID ролей Discord."
)
async def delete_discord_roles_batch(
    request_data_api: StateEntityDiscordBatchDeleteRequest, # Входящая API Pydantic модель
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic) # Используем централизованную зависимость
) -> APIResponse[StateEntityDiscordBatchDeleteResponseData]:
    logger.info("Получен запрос: DELETE /discord/roles/delete-batch")
    try:
        # 1. Вызов НОВОГО метода логики для массового удаления
        # Этот метод в логике принимает guild_id и список discord_role_ids
        result_from_logic = await logic_service.delete_roles_batch_by_role_ids(
            guild_id=request_data_api.guild_id,
            discord_role_ids=request_data_api.role_ids
        )

        deleted_count = result_from_logic.get("deleted_count", 0)
        # Обработка ошибок, если delete_roles_batch_by_role_ids будет их возвращать
        # Сейчас он возвращает только {"deleted_count": N}
        # Если будет возвращать ошибки, нужно добавить их парсинг здесь.

        deleted_details = StateEntityDiscordBatchDeleteResponseData(deleted_count=deleted_count) # Инициализировано корректно

        return create_success_response(
            data=deleted_details,
            message=f"Успешно удалено {deleted_details.deleted_count} ролей Discord из базы данных."
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при пакетном удалении ролей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

# --- Обновленный роут для удаления одной Discord роли по ПК ---
# Путь роута изменен: world_id удален, access_code удален из пути, т.к. ПК теперь (guild_id, discord_role_id)
@router.delete(
    "/roles/guild/{guild_id}/role/{role_id}", # Изменено: Удалены /world/{world_id}/access/{access_code}
    response_model=APIResponse[Dict[str, Any]],
    summary="Удалить Discord роль по ID гильдии и ID роли",
    description="Удаляет запись о Discord роли из базы данных по ID гильдии и ID роли."
)
async def delete_discord_role_by_primary_key(
    guild_id: int,
    role_id: int,
    # access_code: str, # Удалено из аргументов функции
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic)
) -> APIResponse[Dict[str, Any]]:
    logger.info(f"Получен запрос: DELETE /discord/roles/guild/{guild_id}/role/{role_id}")
    try:
        # 1. Преобразование входящих параметров в Internal DTO Command (StateEntityDiscordDeleteCommand)
        # DTO теперь принимает только guild_id и discord_role_id
        delete_command = StateEntityDiscordDeleteCommand(
            guild_id=guild_id,
            discord_role_id=role_id,
            # access_code="N/A" # Больше не нужно, так как DTO был изменен
        )

        # 2. Вызов бизнес-логики с DTO-командой
        result = await logic_service.delete_entity_by_primary_key(delete_command)

        if result.get("deleted_count", 0) > 0:
            return create_success_response(message=f"Роль (Guild ID: {guild_id}, Role ID: {role_id}) успешно удалена.", data=result)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(code="ROLE_NOT_FOUND", message=f"Роль (Guild ID: {guild_id}, Role ID: {role_id}) не найдена для удаления.").model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при удалении роли по PK (Guild: {guild_id}, Role: {role_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

# --- ОБНОВЛЕННЫЙ роут для получения одной Discord роли по ПК ---
# Путь роута изменен: access_code удален из пути, т.к. ПК теперь (guild_id, discord_role_id)
@router.get(
    "/roles/guild/{guild_id}/role/{role_id}", # Изменено: Удалены /world/{world_id}/access/{access_code}
    response_model=APIResponse[StateEntityDiscordAPIResponse],
    summary="Получить Discord роль по ID гильдии и ID роли",
    description="Получает запись о Discord роли из базы данных по ID гильдии и ID роли."
)
async def get_discord_role_by_primary_key(
    guild_id: int,
    role_id: int,
    # access_code: str, # Удалено из аргументов функции
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic)
) -> APIResponse[StateEntityDiscordAPIResponse]:
    logger.info(f"Получен запрос: GET /discord/roles/guild/{guild_id}/role/{role_id}")
    try:
        # Вызов логики get_entity_by_primary_key (теперь принимает только guild_id и discord_role_id)
        entity_dto: StateEntityDiscordDTO = await logic_service.get_entity_by_primary_key(
            guild_id=guild_id,
            discord_role_id=role_id
        )

        if not entity_dto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(code="ROLE_NOT_FOUND", message=f"Роль не найдена.").model_dump()
            )
        
        return create_success_response(
            data=StateEntityDiscordAPIResponse(**entity_dto.model_dump()),
            message=f"Роль успешно получена."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении роли по PK: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

# --- НОВЫЙ роут для создания/обновления одной Discord роли (по ПК) ---
# Использование PUT для idempotency (повторный вызов с тем же PK дает тот же результат)
@router.put(
    "/roles/guild/{guild_id}/role/{role_id}",
    response_model=APIResponse[StateEntityDiscordAPIResponse],
    summary="Создать или обновить Discord роль по ID гильдии и ID роли",
    description="Создает новую запись о Discord роли или обновляет существующую в базе данных. В теле запроса должен быть 'access_code'."
)
async def create_or_update_discord_role(
    guild_id: int, # Из пути
    role_id: int,  # Из пути
    request_body: StateEntityDiscordCreateUpdateRequest, # Тело запроса, содержит access_code и description
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic)
) -> APIResponse[StateEntityDiscordAPIResponse]:
    logger.info(f"Получен запрос на создание/обновление Discord роли: Guild ID={guild_id}, Role ID={role_id}, Access Code={request_body.access_code}")
    try:
        # 1. Преобразование входящих данных в Internal DTO Command (StateEntityDiscordCreateUpdateCommand)
        # Объединяем параметры из пути с данными из тела запроса
        create_update_command = StateEntityDiscordCreateUpdateCommand(
            guild_id=guild_id,
            discord_role_id=role_id,
            access_code=request_body.access_code,
            description=request_body.description
        )

        # 2. Вызов бизнес-логики для массового создания/обновления (оборачиваем одну команду в список)
        batch_command = StateEntitiesDiscordBatchCreateCommand(roles_batch=[create_update_command])
        result_from_logic = await logic_service.create_roles_discord(batch_command) # Этот метод выполняет upsert

        # Логика create_roles_discord возвращает Dict[str, Any], содержащий {'created': N, 'updated': M}
        if result_from_logic.get('created', 0) > 0 or result_from_logic.get('updated', 0) > 0:
            # После создания/обновления получаем актуальную сущность для возврата
            # Здесь вызывается get_entity_by_primary_key для получения полной актуальной DTO
            actual_entity_dto: StateEntityDiscordDTO = await logic_service.get_entity_by_primary_key(
                guild_id=guild_id,
                discord_role_id=role_id
            )
            
            if not actual_entity_dto:
                # Крайне маловероятно после успешного upsert, но для надежности
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=create_error_response(code="RETRIEVAL_ERROR", message="Не удалось получить созданную/обновленную роль.").model_dump())

            message = "Роль успешно создана/обновлена."
            if result_from_logic.get('created', 0) > 0:
                message = "Роль успешно создана."
            elif result_from_logic.get('updated', 0) > 0:
                message = "Роль успешно обновлена."

            return create_success_response(
                data=StateEntityDiscordAPIResponse(**actual_entity_dto.model_dump()),
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(code="CREATE_UPDATE_ERROR", message="Не удалось создать/обновить роль.").model_dump()
            )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Ошибка валидации при создании/обновлении роли: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code="VALIDATION_ERROR", message=str(e)).model_dump()
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании/обновлении роли: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

# --- Обновленный роут для получения всех Discord ролей для гильдии ---
@router.get(
    "/roles/guild/{guild_id}",
    response_model=APIResponse[List[StateEntityDiscordAPIResponse]], # Используем API-модель для списка
    summary="Получить все Discord роли для гильдии",
    description="Возвращает список всех сущностей Discord ролей, сохраненных для указанного ID гильдии."
)
async def get_all_discord_roles_for_guild(
    guild_id: int,
    logic_service: StateEntitiesDiscordLogic = Depends(get_state_entities_discord_logic)
) -> APIResponse[List[StateEntityDiscordAPIResponse]]:
    logger.info(f"Получен запрос на получение всех Discord ролей для гильдии {guild_id}")
    try:
        # 1. Вызов бизнес-логики, которая возвращает список DTO-моделей
        entities_list_of_dtos: List[StateEntityDiscordDTO] = await logic_service.get_all_entities_for_guild(guild_id)

        # 2. Преобразование списка DTO-моделей в список API Response-моделей
        entities_api_responses = [StateEntityDiscordAPIResponse(**entity_dto.model_dump()) for entity_dto in entities_list_of_dtos]

        return create_success_response(
            data=entities_api_responses,
            message=f"Успешно получено {len(entities_api_responses)} Discord ролей для гильдии {guild_id}."
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении ролей Discord для гильдии {guild_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при получении данных.").model_dump()
        )


discord_roles_mapping_router = router