import discord

# Основные роли
DEFAULT_ROLE = "Странник"  # Эта роль, видимо, не используется в game-server, а нужна для хаба
OFFLINE_ROLE = "Offline player status"  # ИЗМЕНЕНО
ONLINE_ROLE = "Online player status"   # ИЗМЕНЕНО
ADMIN_ROLE = "Администратор"
MOD_ROLE = "Модератор"
TESTER_ROLE = "Тестер"
PLAYER_ROLE = "Игрок" # ДОБАВЛЕНО

# Шаблон ролей
REQUIRED_ROLES = {
    DEFAULT_ROLE: {"color": discord.Color.light_gray()},
    OFFLINE_ROLE: {"color": discord.Color.orange()},
    ONLINE_ROLE: {"color": discord.Color.green()},
    ADMIN_ROLE: {"color": discord.Color.red()},
    MOD_ROLE: {"color": discord.Color.blue()},
    TESTER_ROLE: {"color": discord.Color.yellow()},
    PLAYER_ROLE: {"color": discord.Color.default()} # ДОБАВЛЕНО
}