# game_server/Logic/ApplicationLogic/api_reg/auth_service.py

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Any, Dict, Optional, List

# Импортируем Pydantic-модели из нашего пакета api_models
from game_server.api_fast.api_models.system_api import (
    AuthData, PlayerData, LinkingUrlData, RegisterOrLoginRequest, CharacterLoginSummary, CharacterSummary
)
# Импортируем утилиты и менеджеры
from .utils.account_helpers import generate_auth_token, generate_linking_token, get_linking_token_expiry_time, generate_next_guest_username
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.character.character_meta.ORM_character import CharacterRepository
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.accaunt.ORM_accaunt import AccountInfoManager

logger = logging.getLogger(__name__)

# Определяем кастомные исключения для сервиса
class AuthServiceError(Exception):
    """Базовое исключение для ошибок сервиса аутентификации."""
    pass

class AccountNotFound(AuthServiceError):
    """Исключение для случаев, когда аккаунт или токен не найден."""
    pass


class AuthService:
    """Сервис для операций аутентификации с инъекцией зависимостей."""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.account_manager = AccountInfoManager(db_session)
        self.character_repo = CharacterRepository(db_session)

    async def create_or_link_account(self, request_data: RegisterOrLoginRequest) -> AuthData:
        """
        Создаёт или обновляет аккаунт.
        Возвращает Pydantic-модель AuthData или выбрасывает исключение AuthServiceError.
        """
        try:
            account = await self.account_manager.get_account_by_identifier(
                request_data.identifier_type, request_data.identifier_value
            )
            
            if account:
                # Аккаунт существует -> обновляем токен и возвращаем данные
                update_data = {
                    "auth_token": await generate_auth_token(),
                    "linked_platforms": {**account.linked_platforms, request_data.identifier_type: request_data.identifier_value}
                }
                updated_account = await self.account_manager.update_account(
                    account.account_id, update_data
                )
                characters = await self.character_repo.get_characters_by_account_id(updated_account.account_id)
                result_chars = [CharacterLoginSummary.model_validate(c) for c in characters]
                
                await self.db_session.commit()
                return AuthData(
                    account_id=updated_account.account_id,
                    auth_token=updated_account.auth_token,
                    character_ids=result_chars
                )
            else:
                # Аккаунт не существует -> создаем новый
                all_guests = await self.account_manager.get_all_guest_usernames()
                username = await generate_next_guest_username(all_guests)
                
                # --- ИСПРАВЛЕННЫЙ БЛОК ---
                # Заменяем плейсхолдер на полный набор полей для нового аккаунта
                account_data = {
                    "username": username,
                    "avatar": request_data.avatar,
                    "locale": request_data.locale,
                    "region": request_data.region,
                    "status": "active",
                    "role": "user",
                    "twofa_enabled": False,
                    "auth_token": await generate_auth_token(),
                    "linked_platforms": {request_data.identifier_type: request_data.identifier_value},
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }

                new_account = await self.account_manager.create_account(account_data)
                await self.db_session.commit()
                
                return AuthData(
                    account_id=new_account.account_id, auth_token=new_account.auth_token, character_ids=[]
                )

        except Exception as e:
            await self.db_session.rollback()
            logger.exception("Error in create_or_link_account")
            raise AuthServiceError(f"Ошибка при операции с аккаунтом: {e}")

    async def get_player_full_data(self, auth_token: str) -> PlayerData:
        """
        Получает полные данные игрока.
        Возвращает Pydantic-модель PlayerData или выбрасывает AccountNotFound.
        """
        account = await self.account_manager.get_account_by_auth_token(auth_token)
        if not account:
            raise AccountNotFound("Недействительный или просроченный токен аутентификации.")

        all_chars_orm = await self.character_repo.get_characters_by_account_id(account.account_id)
        active_char_orm = await self.character_repo.get_online_character_by_account_id(account.account_id)
        
        # --- ИСПРАВЛЕННЫЙ БЛОК ---
        # Заменяем плейсхолдер "..." на полный набор полей из вашего оригинального кода.
        # Предполагается, что все эти атрибуты есть у ORM-модели 'account'.
        account_data_dict = {
            "account_id": account.account_id,
            "username": account.username,
            "email": account.email,
            "avatar": account.avatar,
            "locale": account.locale,
            "region": account.region,
            "status": account.status,
            "role": account.role,
            "twofa_enabled": account.twofa_enabled,
            "linked_platforms": account.linked_platforms,
        }

        characters_list = [CharacterSummary.model_validate(c) for c in all_chars_orm if not c.is_deleted]
        active_character = CharacterSummary.model_validate(active_char_orm) if active_char_orm else None

        return PlayerData(
            account_info=account_data_dict,
            characters=characters_list,
            active_character_id=active_char_orm.character_id if active_char_orm else None,
            active_character_summary=active_character
        )

    async def generate_linking_url(self, auth_token: str) -> LinkingUrlData:
        account = await self.account_manager.get_account_by_auth_token(auth_token)
        if not account:
            raise AccountNotFound("Недействительный или просроченный токен аутентификации.")

        token = await generate_linking_token()
        expiry = get_linking_token_expiry_time(minutes=30)
        
        # ... логика сохранения токена в БД ...
        await self.db_session.commit()
        
        return LinkingUrlData(
            linking_token=token,
            linking_url=f"YOUR_FRONTEND_URL/link?token={token}", # Заменить на реальный URL
            expires_at=expiry.isoformat()
        )
        
    async def get_shard_for_discord_user(self, request_data: RegisterOrLoginRequest) -> Dict[str, Any]:
        """
        Находит или создает аккаунт по Discord ID, определяет подходящий шард
        и возвращает информацию для генерации инвайта.
        """
        try:
            # Шаг 1: Найти или создать основной аккаунт (почти как в create_or_link_account)
            account = await self.account_manager.get_account_by_identifier(
                "discord", request_data.identifier_value
            )

            if not account:
                # Если аккаунта нет, создаем его
                all_guests = await self.account_manager.get_all_guest_usernames()
                username = await generate_next_guest_username(all_guests)
                
                account_data = {
                    "username": username, "avatar": request_data.avatar,
                    "locale": request_data.locale, "region": request_data.region,
                    "auth_token": await generate_auth_token(),
                    "linked_platforms": {"discord": request_data.identifier_value}
                }
                account = await self.account_manager.create_account(account_data)
                # Важно: здесь же нужно создать и связанную запись в account_game_data
                # ... (код для создания account_game_data)
                await self.db_session.commit()
                
            # Шаг 2: Определить ID шарда
            game_data = await self.account_manager.get_game_data(account.account_id)
            
            shard_id = None
            if game_data and game_data.shard_id:
                # Если у игрока уже есть шард, возвращаем его
                shard_id = game_data.shard_id
                is_new_player_on_shard = False
            else:
                # Если шарда нет (новый игрок или вернувшийся старый без шарда)
                # -> Запускаем логику выбора шарда для новичка
                # TODO: Реализовать логику выбора шарда (например, наименее загруженный)
                shard_id = "default_shard_id_123" # Временная заглушка
                is_new_player_on_shard = True
                # Здесь же можно обновить запись в account_game_data, прописав ему новый шард
                # ...

            await self.db_session.commit()

            # Шаг 3: Вернуть результат
            return {
                "account_id": account.account_id,
                "shard_id": shard_id,
                "is_new_player": not (game_data and game_data.shard_id)
            }

        except Exception as e:
            await self.db_session.rollback()
            logger.exception("Ошибка в get_shard_for_discord_user")
            raise AuthServiceError(f"Ошибка при определении шарда для пользователя: {e}")