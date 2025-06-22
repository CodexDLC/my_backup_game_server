# Logic/DomainLogic/utils/export_service.py
# Импортируем вашу существующую функцию


from game_server.database.script_import.export_yaml import export_to_yaml


class ExportError(Exception):
    """Кастомное исключение для ошибок экспорта."""
    pass

class ExportService:
    """Сервис-обертка для запуска утилиты экспорта."""
    async def export_schema_to_yaml(self, schema_name: str) -> str:
        try:
            # Сервис просто вызывает ваш скрипт.
            # Скрипт сам управляет своим подключением к БД.
            folder_path = await export_to_yaml(schema_name)
            return folder_path
        except Exception as e:
            # Любую ошибку из скрипта "заворачиваем" в нашу ошибку сервиса
            raise ExportError(f"Ошибка во время выполнения скрипта экспорта: {e}")