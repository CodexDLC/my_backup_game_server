# game_server/app_discord_bot/app/startup/ui_initializer/ui_initializer.py
import discord
from discord.ext import commands # Для bot.add_view
import inject
import logging

from game_server.app_discord_bot.app.ui.views.authentication.login_view import LoginView
from game_server.app_discord_bot.app.ui.views.authentication.registration_view import RegistrationView




# Импортируем все классы постоянных View, которые нужно отслеживать
# Убедитесь, что пути импорта корректны для вашей структуры проекта


# Реестр всех постоянных View, которые бот должен отслеживать
# Важно: здесь указываем КЛАССЫ View, а не их экземпляры.
PERSISTENT_VIEWS = [
    RegistrationView, 
    LoginView, 
]

class UIInitializer:
    """
    Класс, отвечающий за инициализацию и перепривязку постоянных Discord UI View.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
        self.logger.info("✨ UIInitializer инициализирован.")

    async def initialize_persistent_views(self):
        """
        Инициализирует и добавляет все постоянные View к боту.
        Это должно вызываться при каждом запуске бота (например, в on_ready).
        """
        self.logger.info("Начало инициализации постоянных Discord UI Views...")
        for ViewClass in PERSISTENT_VIEWS:
            try:
                # Если ViewClass требует bot_instance при init, передаем его
                # Если ViewClass использует @inject.autoparams() для своих зависимостей,
                # то inject.call(ViewClass) сам разрешит их.
                if hasattr(ViewClass, '__init__') and 'bot_instance' in ViewClass.__init__.__code__.co_varnames:
                    # Создаем экземпляр View, передавая bot_instance, если конструктор его ожидает
                    view_instance = ViewClass(bot_instance=self.bot)
                else:
                    # Если View не имеет bot_instance в __init__ (или сам использует @inject.autoparams())
                    # inject.call попытается разрешить все зависимости конструктора.
                    # В этом случае bot_instance должен быть забинжен в DI-контейнере.
                    view_instance = inject.call() # Предполагается, что bot будет разрешен через DI, если нужен.
                                                          # Если ViewClass все еще требует 'bot' напрямую,
                                                          # убедитесь, что он забинжен как discord.Client.
                self.bot.add_view(view_instance)
                self.logger.info(f"Добавлен постоянный View: {type(view_instance).__name__}")
            except Exception as e:
                self.logger.error(f"Ошибка при добавлении постоянного View {ViewClass.__name__}: {e}", exc_info=True)
        self.logger.info("Инициализация постоянных Discord UI Views завершена.")