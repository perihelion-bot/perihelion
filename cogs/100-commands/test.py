import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

class TestingCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

    # This is left intentionally untranslated.

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: testing loaded")

    @app_commands.command(name="test", description="A testing command.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("""This is a test command.""", ephemeral=True)

    @app_commands.command(name="test_usersettings", description="A testing command. Gets all your settings directly in Python dictionary form.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def test_usersettings(self, interaction: discord.Interaction):
        await interaction.response.send_message(get_data_manager("user", interaction.user.id), ephemeral=True)

    @app_commands.command(name="test_err", description="A testing command, for errors.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def test_err(self, interaction: discord.Interaction):
        raise Exception("Oops! You forgot to put the CD in your computer.")

async def setup(client):
    await client.add_cog(TestingCog(client))
