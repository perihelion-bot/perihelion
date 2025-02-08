import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

import cexprtk

class CalculationCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: calc loaded")

    @app_commands.command(name="command_calc", description="command_calc")
    @app_commands.rename(equ="command_calc_equ")
    @app_commands.describe(equ="command_calc_equ")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def calc(self, interaction: discord.Interaction, equ: str):
        await interaction.response.send_message(cexprtk.evaluate_expression(equ, {}))

async def setup(client):
    await client.add_cog(CalculationCog(client))
