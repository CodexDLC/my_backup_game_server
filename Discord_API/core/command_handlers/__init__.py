# discord_bot/command_handlers/__init__.py

# Импортируем сам реестр и декоратор, чтобы они были доступны из пакета
from Discord_API.core.command_handlers.registry import COMMAND_HANDLERS, register_handler

# Импортируем все наши файлы с обработчиками.
# Этот импорт заставит Python выполнить код в этих файлах,
# что приведет к регистрации функций-обработчиков в реестре COMMAND_HANDLERS.
from . import cleanup_handlers
# from . import broadcast_handlers # <-- раскомментируете, когда создадите этот файл