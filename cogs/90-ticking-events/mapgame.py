import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

class MapGameCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: mapgame loaded")
    
    def mapgame_step(self):
        ...
        

    @app_commands.command(name="command_mapgame", description="command_mapgame")
    @app_commands.rename(arg1="command_mapgame_arg1")
    @app_commands.describe(arg1="command_mapgame_arg1")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def mapgame(self, interaction: discord.Interaction, arg1: Optional[app_commands.Range[int, 1, 10]]):
        settings = get_data_manager("user", interaction.user.id)
        self.mapgame_step()
        
async def setup(client):
    await client.add_cog(MapGameCog(client))
