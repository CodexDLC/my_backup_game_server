# game_server/app_discord_bot/app/ui/embed_factories/list_embed_factory.py

import discord
from typing import List, Dict

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import InspectionListDTO


def _format_entities_as_numbered_list(entities: List, start_index: int = 1) -> str:
    """Вспомогательная функция для форматирования списка в пронумерованный текст."""
    return "\n".join([f"**{start_index + i}.** {entity.label}" for i, entity in enumerate(entities)])

def create_player_list_embeds(dto: InspectionListDTO) -> List[discord.Embed]:
    """
    Фабрика для создания эмбедов списка игроков.
    Группирует игроков по статусу (друг, нейтрал, ПК) и создает для каждой группы свой эмбед.
    """
    embeds = []
    
    # 1. Сортируем игроков по группам
    friends = []
    neutrals = []
    pks = []

    for entity in dto.entities:
        # Атрибуты 'is_friend' и 'alignment' должны приходить в DTO из данных
        # Для этого нужно будет обновить InspectedEntityDTO, добавив эти поля
        # Но для заглушки мы можем извлекать их из label
        is_friend = "(Д)" in entity.label
        is_pk = False # В будущем, тут будет проверка по alignment

        if is_friend:
            friends.append(entity)
        elif is_pk:
            pks.append(entity)
        else:
            neutrals.append(entity)
            
    # 2. Создаем эмбеды для каждой непустой группы
    if friends:
        friend_embed = discord.Embed(
            title="Друзья",
            color=discord.Color.blue(),
            description=_format_entities_as_numbered_list(friends)
        )
        embeds.append(friend_embed)

    if neutrals:
        neutral_embed = discord.Embed(
            title="Нейтральные игроки",
            color=discord.Color.light_grey(),
            description=_format_entities_as_numbered_list(neutrals)
        )
        embeds.append(neutral_embed)
        
    if pks:
        pk_embed = discord.Embed(
            title="Опасные игроки",
            color=discord.Color.red(),
            description=_format_entities_as_numbered_list(pks)
        )
        embeds.append(pk_embed)
        
    # Добавляем пагинацию в заголовок первого эмбеда, если он есть
    if embeds:
        embeds[0].title += f" (Страница {dto.pagination.current_page}/{dto.pagination.total_pages})"

    return embeds

def create_default_list_embeds(dto: InspectionListDTO) -> List[discord.Embed]:
    """
    Фабрика по умолчанию. Создает один эмбед с двумя колонками.
    """
    main_embed = discord.Embed(
        title=f"{dto.title} (Страница {dto.pagination.current_page}/{dto.pagination.total_pages})",
        color=discord.Color.blue()
    )

    if dto.entities:
        num_entities = len(dto.entities)
        mid_point = (num_entities + 1) // 2
        col1_entities = dto.entities[:mid_point]
        col2_entities = dto.entities[mid_point:]

        col1_text = _format_entities_as_numbered_list(col1_entities)
        if col1_text:
            main_embed.add_field(name="Объекты", value=col1_text, inline=True)

        col2_text = _format_entities_as_numbered_list(col2_entities, start_index=mid_point)
        if col2_text:
            main_embed.add_field(name="\u200b", value=col2_text, inline=True)
    else:
        main_embed.description = "В этой категории пока ничего нет."
        
    return [main_embed]

# --- РЕЕСТР ФАБРИК ЭМБЕДОВ ---
# Связывает ключ категории с функцией-фабрикой
LIST_EMBED_FACTORIES = {
    "players": create_player_list_embeds
    # Для всех остальных категорий будет использоваться create_default_list_embeds
}