import discord
from discord import ui

async def send_new_message(interaction: discord.Interaction, text: str):
    # Эта функция остается для других нужд
    await interaction.channel.send(text)

async def edit_message(interaction: discord.Interaction, new_text: str, new_view: ui.View):
    """
    Хелпер для редактирования сообщения, с которым произошла интеракция.
    """
    print(f"[+] Хелпер редактирует сообщение: '{new_text}'")
    await interaction.response.edit_message(content=new_text, view=new_view)