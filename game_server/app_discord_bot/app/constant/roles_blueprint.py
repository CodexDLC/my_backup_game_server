import discord

# Основные роли
DEFAULT_ROLE = "Странник"
OFFLINE_ROLE = "Игрок_оф"
ONLINE_ROLE = "Игрок_он"
ADMIN_ROLE = "Администратор"
MOD_ROLE = "Модератор"
TESTER_ROLE = "Тестер"

# Шаблон ролей
REQUIRED_ROLES = {
    DEFAULT_ROLE: {"color": discord.Color.light_gray()},
    OFFLINE_ROLE: {"color": discord.Color.orange()},
    ONLINE_ROLE: {"color": discord.Color.green()},
    ADMIN_ROLE: {"color": discord.Color.red()},
    MOD_ROLE: {"color": discord.Color.blue()},
    TESTER_ROLE: {"color": discord.Color.yellow()}
}
