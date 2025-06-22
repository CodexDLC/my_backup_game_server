# game_server/api_fast/rest_routers/discord/discord_entity.py

from fastapi import APIRouter, Depends, HTTPException, status
import logging
from typing import Dict, Any, List

# Импорты Pydantic моделей для запросов и ответов (из вашего api_fast)
from api_fast.api_models.discord_api import (
    DiscordEntityCreateRequest,
    DiscordEntitySyncRequest,
    DiscordEntitySyncDetails,
    DiscordEntityBatchDeleteRequest,
    DiscordEntityBatchDeleteResponseData,
    DiscordEntityAPIResponse,
    DiscordEntityGetByGuildResponseData
)
# Импорт стандартизированных функций ответа API
from api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response

# Импорт сервисного слоя (бизнес-логики) из ApplicationLogic
from game_server.Logic.ApplicationLogic.DiscordIntegration.discord_binding_logic import DiscordBindingLogic

# Импорт новых DTO-моделей из common_contracts
from common_contracts.discord_integration.discord_commands_and_events import (
    DiscordEntityDTO,
    DiscordEntityCreateCommand,
    DiscordEntitiesSyncCommand,
    DiscordEntitiesDeleteCommand,
    DiscordSyncResultDTO
)

# Импорт общих зависимостей из api_fast/dependencies.py
from api_fast.dependencies import (
    get_discord_binding_logic # Теперь импортируем из dependencies
)

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Роут для синхронизации Discord сущностей ---
@router.post(
    "/sync",
    response_model=APIResponse[DiscordEntitySyncDetails],
    summary="Синхронизация Discord сущностей",
    description="Принимает список сущностей Discord от бота для создания или обновления в базе данных."
)
async def sync_discord_entities_endpoint(
    sync_request_api: DiscordEntitySyncRequest, # Входящая API Pydantic модель
    discord_logic: DiscordBindingLogic = Depends(get_discord_binding_logic) # Используем централизованную зависимость
) -> APIResponse[DiscordEntitySyncDetails]:
    """
    Эндпоинт для пакетной синхронизации сущностей Discord.
    Бот отправляет сюда данные после создания/обновления сущностей в Discord.
    """
    logger.info(f"Получен запрос на синхронизацию Discord сущностей для гильдии {sync_request_api.guild_id}")
    try:
        # 1. Преобразование API Model (DiscordEntitySyncRequest) в Internal DTO Command (DiscordEntitiesSyncCommand)
        entity_create_commands: List[DiscordEntityCreateCommand] = [
            DiscordEntityCreateCommand(**entity.model_dump()) for entity in sync_request_api.entities
        ]
        
        sync_command = DiscordEntitiesSyncCommand(
            guild_id=sync_request_api.guild_id,
            entities_data=entity_create_commands
        )

        # 2. Вызов бизнес-логики с DTO-командой
        result_dto: DiscordSyncResultDTO = await discord_logic.sync_discord_entities_to_db(sync_command)

        # 3. Преобразование Internal DTO (DiscordSyncResultDTO) обратно в API Response Model (DiscordEntitySyncDetails)
        processed_api_responses = [DiscordEntityAPIResponse(**entity_dto.model_dump()) for entity_dto in result_dto.processed_entities]

        sync_details = DiscordEntitySyncDetails(
            created_count=result_dto.created_count,
            updated_count=result_dto.updated_count,
            deleted_count=result_dto.deleted_count,
            errors=result_dto.errors,
            processed_entities=processed_api_responses
        )

        if sync_details.errors:
            return create_error_response(
                code="PARTIAL_SYNC_ERROR",
                message=f"Синхронизация завершена с ошибками. Создано: {sync_details.created_count}, Обновлено: {sync_details.updated_count}.",
                data=sync_details
            )

        return create_success_response(
            data=sync_details,
            message=f"Синхронизация завершена успешно. Создано: {sync_details.created_count}, Обновлено: {sync_details.updated_count}."
        )
    except ValueError as e:
        logger.warning(f"Ошибка валидации при синхронизации сущностей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code="VALIDATION_ERROR", message=str(e)).model_dump()
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при синхронизации сущностей Discord: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при синхронизации.").model_dump()
        )

# --- Роут для создания одной Discord сущности ---
@router.post(
    "/create-one",
    response_model=APIResponse[DiscordEntityAPIResponse],
    summary="Создать одну Discord сущность",
    description="Принимает данные об одной сущности Discord от бота для сохранения в базе данных."
)
async def create_single_discord_entity_endpoint(
    entity_data_api: DiscordEntityCreateRequest, # Входящая API Pydantic модель
    discord_logic: DiscordBindingLogic = Depends(get_discord_binding_logic) # Используем централизованную зависимость
) -> APIResponse[DiscordEntityAPIResponse]:
    """
    Эндпоинт для создания одной сущности Discord (например, новой статьи).
    Бот отправляет сюда данные после создания сущности в Discord.
    """
    logger.info(f"Получен запрос на создание одиночной Discord сущности: {entity_data_api.name}")
    try:
        # 1. Преобразование API Model (DiscordEntityCreateRequest) в Internal DTO Command (DiscordEntityCreateCommand)
        create_command = DiscordEntityCreateCommand(**entity_data_api.model_dump())

        # 2. Вызов бизнес-логики с DTO-командой
        new_entity_dto: DiscordEntityDTO = await discord_logic.create_single_discord_entity_in_db(create_command)

        # 3. Преобразование Internal DTO (DiscordEntityDTO) обратно в API Response Model (DiscordEntityAPIResponse)
        new_entity_api = DiscordEntityAPIResponse(**new_entity_dto.model_dump())

        return create_success_response(
            data=new_entity_api,
            message="Сущность Discord успешно создана в базе данных."
        )
    except ValueError as e:
        logger.warning(f"Ошибка при создании одиночной сущности: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code="CREATION_ERROR", message=str(e)).model_dump()
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании одиночной сущности Discord: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при создании.").model_dump()
        )

# --- Роут для пакетного удаления Discord сущностей ---
@router.delete(
    "/batch",
    response_model=APIResponse[DiscordEntityBatchDeleteResponseData],
    summary="Удалить Discord сущности пакетом",
    description="Принимает список Discord ID сущностей от бота для удаления из базы данных."
)
async def delete_discord_entities_batch_endpoint(
    delete_request_api: DiscordEntityBatchDeleteRequest, # Входящая API Pydantic модель
    discord_logic: DiscordBindingLogic = Depends(get_discord_binding_logic) # Используем централизованную зависимость
) -> APIResponse[DiscordEntityBatchDeleteResponseData]:
    """
    Эндпоинт для пакетного удаления сущностей Discord.
    Бот отправляет сюда запрос после удаления сущностей в Discord.
    """
    logger.info(f"Получен запрос на пакетное удаление Discord сущностей для гильдии {delete_request_api.guild_id}")
    try:
        # 1. Преобразование API Model (DiscordEntityBatchDeleteRequest) в Internal DTO Command (DiscordEntitiesDeleteCommand)
        delete_command = DiscordEntitiesDeleteCommand(**delete_request_api.model_dump())

        # 2. Вызов бизнес-логики с DTO-командой
        delete_details_dict = await discord_logic.delete_discord_entities_from_db(delete_command)

        # 3. Преобразование словаря обратно в API Response Model (DiscordEntityBatchDeleteResponseData)
        delete_details = DiscordEntityBatchDeleteResponseData(**delete_details_dict)

        return create_success_response(
            data=delete_details,
            message=f"Успешно удалено {delete_details.deleted_count} сущностей Discord из базы данных."
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при пакетном удалении сущностей Discord: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при удалении.").model_dump()
        )

# --- Роут для получения всех Discord сущностей для гильдии ---
@router.get(
    "/{guild_id}",
    response_model=APIResponse[DiscordEntityGetByGuildResponseData],
    summary="Получить все Discord сущности для гильдии",
    description="Возвращает список всех сущностей Discord, сохраненных для указанного ID гильдии."
)
async def get_discord_entities_by_guild_endpoint(
    guild_id: int,
    discord_logic: DiscordBindingLogic = Depends(get_discord_binding_logic) # Используем централизованную зависимость
) -> APIResponse[DiscordEntityGetByGuildResponseData]:
    """
    Эндпоинт для получения всех сущностей Discord для конкретной гильдии.
    Используется ботом для получения списка сущностей (например, для последующего удаления).
    """
    logger.info(f"Получен запрос на получение Discord сущностей для гильдии {guild_id}")
    try:
        # 1. Вызов бизнес-логики, которая теперь возвращает список DTO-моделей
        entities_list_of_dtos: List[DiscordEntityDTO] = await discord_logic.get_discord_entities_from_db(guild_id)

        # 2. Преобразование списка DTO-моделей в список API Response-моделей
        entities_api_responses = [DiscordEntityAPIResponse(**entity_dto.model_dump()) for entity_dto in entities_list_of_dtos]

        return create_success_response(
            data=DiscordEntityGetByGuildResponseData(entities=entities_api_responses),
            message=f"Успешно получено {len(entities_api_responses)} сущностей Discord для гильдии {guild_id}."
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении сущностей Discord для гильдии {guild_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при получении данных.").model_dump()
        )

# Экспорт роутера для использования в локальном конфиге
discord_entity_router = router