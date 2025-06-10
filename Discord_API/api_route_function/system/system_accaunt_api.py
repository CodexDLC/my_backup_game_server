


import requests
from Discord_API.discord_settings import API_URL


class DiscordCreateAccount:
    def __init__(self, user_id: str, username: str, avatar_url: str = None, locale: str = None, region: str = None):
        """Инициализация с данными от Discord"""
        self.identifier_type = "discord_id"
        self.identifier_value = user_id
        self.username = username
        self.avatar_url = avatar_url
        self.locale = locale
        self.region = region

    def send_to_api(self, endpoint: str, payload: dict):
        """Отправляет запрос в API"""
        response = requests.post(f"{API_URL}/{endpoint}", json=payload)
        return response.json() if response.status_code == 200 else {"status": "error", "message": "Ошибка запроса"}

    def create_account(self):
        """Создаёт или обновляет аккаунт"""
        payload = {
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
            "username": self.username,
            "avatar": self.avatar_url,
            "locale": self.locale,
            "region": self.region,
        }
        return self.send_to_api("create_account", payload)

    def update_account(self, update_data: dict):
        """Обновляет данные аккаунта"""
        payload = {
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
            "update_data": update_data,
        }
        return self.send_to_api("update_account", payload)

    def delete_account(self):
        """Удаляет аккаунт"""
        payload = {
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
        }
        return self.send_to_api("delete_account", payload)

    def generate_registration_link(self):
        """Генерирует ссылку на регистрацию"""
        payload = {
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
        }
        return self.send_to_api("generate_registration_link", payload)
    
    async def get_account_discord(user_id: str):
        """Проверяет, есть ли аккаунт у пользователя"""
        payload = {"identifier_type": "discord_id", "identifier_value": user_id}
        response = requests.get(f"{API_URL}/get_account", json=payload)
        return response.json()
