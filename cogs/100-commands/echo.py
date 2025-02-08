import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

class EchoCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: echo loaded")

    @app_commands.command(name="command_echo", description="command_echo")
    @app_commands.describe(message="command_echo_message")
    @app_commands.rename(message="command_echo_message")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def echo(self, interaction: discord.Interaction, message: str):
        message = discord.utils.escape_mentions(message)
        await interaction.response.send_message(f"{message}\n-# echoed by {interaction.user.mention}")
        
async def setup(client):
    await client.add_cog(EchoCog(client))
