import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str


class DefineCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.language = client.get_cog('language')

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: define loaded")

    @app_commands.command(name="command_define", description="command_define")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def define(self, interaction: discord.Interaction, word: str):

        settings = get_data_manager("user", interaction.user.id)

        data = self.language.define(word)
        if settings["Define: English-only"]:
            stringout = self.language.english_json_to_markdown(data)
            await interaction.response.send_message(embed=embed_template(interaction, f"{word}", stringout), ephemeral=True)
            return

        try:
            stringout = self.language.json_to_markdown(data)
            await interaction.response.send_message(embed=embed_template(interaction, word, stringout), ephemeral=True)
        except Exception:
            stringout = self.language.english_json_to_markdown(data)
            await interaction.response.send_message(embed=embed_template(interaction, f"{word} (english definitions only for length)", stringout), ephemeral=True)

async def setup(client):
    await client.add_cog(DefineCog(client))
