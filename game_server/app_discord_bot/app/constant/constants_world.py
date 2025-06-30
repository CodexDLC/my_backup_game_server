# Discord_API\constant\constants_world.py

HUB_GUILD_ID = 1366038189147684906
REGISTRATION_CHANNEL_ID = 1384961119633932398

# --- Диапазоны Access Codes для публичных/общедоступных локаций ---
# Каналы с access_code в этом диапазоне будут получать роль "Онлайн".
PUBLIC_ACCESS_CODES_START = 1001
PUBLIC_ACCESS_CODES_END = 1004

# --- Access Codes для системных ролей (из game_server API) ---
# Эти коды соответствуют определенным системным ролям в вашей игровой логике.
# Используются для идентификации системных ролей, приходящих из entities_discord.
SYSTEM_ACCESS_CODE_ADMIN = 1
SYSTEM_ACCESS_CODE_MODERATOR = 2
SYSTEM_ACCESS_CODE_TESTER = 3
SYSTEM_ACCESS_CODE_ONLINE = 101
SYSTEM_ACCESS_CODE_OFFLINE = 102
SYSTEM_ACCESS_CODE_CHARACTER_SELECTION = 4 # <--- Добавлено

# Множество системных access_code для удобства проверки.
SYSTEM_ACCESS_CODES_SET = {
    SYSTEM_ACCESS_CODE_ADMIN,
    SYSTEM_ACCESS_CODE_MODERATOR,
    SYSTEM_ACCESS_CODE_TESTER,
    SYSTEM_ACCESS_CODE_ONLINE,
    SYSTEM_ACCESS_CODE_OFFLINE,
    SYSTEM_ACCESS_CODE_CHARACTER_SELECTION,
}

# --- Системные строковые названия ролей для `system_roles_map` ---
# Эти названия должны соответствовать ключам, которые вы хотите использовать
# в словаре `system_roles_map`, и могут быть сопоставлены с `role_name` из API.
SYSTEM_ROLE_KEY_ADMIN = "admin"
SYSTEM_ROLE_KEY_MODERATOR = "moderator"
SYSTEM_ROLE_KEY_ONLINE = "online"
SYSTEM_ROLE_KEY_OFFLINE = "offline"
SYSTEM_ROLE_KEY_TESTER = "tester"
SYSTEM_ROLE_KEY_CHARACTER_SELECTION = "character_selection"

# Соответствия строковых названий ролей из API к внутренним ключам system_roles_map.
# Это позволяет поддерживать несколько вариантов названий ролей в API
# (например, "admin" и "администратор" ведут к одному ключу `SYSTEM_ROLE_KEY_ADMIN`).
ROLE_NAME_MAPPING = {
    "admin": SYSTEM_ROLE_KEY_ADMIN,
    "администратор": SYSTEM_ROLE_KEY_ADMIN,
    "moderator": SYSTEM_ROLE_KEY_MODERATOR,
    "модератор": SYSTEM_ROLE_KEY_MODERATOR,
    "online": SYSTEM_ROLE_KEY_ONLINE,
    "онлайн": SYSTEM_ROLE_KEY_ONLINE,
    "offline": SYSTEM_ROLE_KEY_OFFLINE,
    "оффлайн": SYSTEM_ROLE_KEY_OFFLINE,
    "tester": SYSTEM_ROLE_KEY_TESTER,
    "тестер": SYSTEM_ROLE_KEY_TESTER,
    "character selection": SYSTEM_ROLE_KEY_CHARACTER_SELECTION,
    "выбор персонажа": SYSTEM_ROLE_KEY_CHARACTER_SELECTION,
}

# --- Стандартные наборы разрешений для `discord.PermissionOverwrite` ---

# Разрешения, которые ЗАПРЕЩАЮТСЯ по умолчанию (например, для роли @everyone).
# Важно: `False` означает "запретить".
DEFAULT_DENY_PERMISSIONS = {
    "view_channel": False,
    "read_messages": False,
    "send_messages": False,
    "add_reactions": False,
    "use_external_emojis": False,
    "send_tts_messages": False,
    "connect": False, # Добавлено для голосовых каналов
    "speak": False,   # Добавлено для голосовых каналов
    "stream": False,  # Добавлено для голосовых каналов
    "use_application_commands": False, # Добавлено для слеш-команд
}

# Разрешения, которые РАЗРЕШАЮТСЯ по умолчанию для ролей, которым нужен только просмотр и чтение истории.
DEFAULT_ALLOW_READ_ONLY_PERMISSIONS = {
    "view_channel": True,
    "read_messages": True,
    "read_message_history": False,
}

# Разрешения для ролей, которым нужен просмотр, чтение и взаимодействие с кнопками/реакциями (без возможности отправки сообщений).
DEFAULT_ALLOW_BUTTON_INTERACTION_PERMISSIONS = {
    "view_channel": True,
    "read_messages": True,
    "read_message_history": True,
    "send_messages": False, # Явно запрет отправки сообщений в чат
    "add_reactions": True, # Разрешить добавление реакций (для кнопок/оценок)
    "use_external_emojis": True, # Разрешить использование внешних эмодзи (для кнопок/реакций)
    "send_tts_messages": False,
    "use_application_commands": True, # Разрешено использование слеш-команд
    # Для голосовых каналов:
    "connect": True,
    "speak": True,
    "stream": True, # Если нужно разрешить стриминг
}

# Разрешения, которые РАЗРЕШАЮТСЯ для полноценного участия (для админов/модераторов).
# Это должен быть максимально полный набор прав для управления сервером.
DEFAULT_ALLOW_FULL_PERMISSIONS = {
    "view_channel": True,
    "read_messages": True,
    "read_message_history": True,
    "send_messages": True,
    "add_reactions": True,
    "use_external_emojis": True,
    "send_tts_messages": True,
    "manage_channels": True,
    "manage_roles": True,
    "manage_webhooks": True,
    "manage_messages": True,
    "embed_links": True,
    "attach_files": True,
    "kick_members": True,
    "ban_members": True,
    "move_members": True,
    "mute_members": True,
    "deafen_members": True,
    "priority_speaker": True,
    "stream": True,
    "use_application_commands": True,
    "connect": True,
    "speak": True,
    "administrator": True, # Обычно администраторы имеют это разрешение, дающее все остальные

}