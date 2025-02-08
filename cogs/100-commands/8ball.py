import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from assets.eightball_responses import responses

import random

class EightBallCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: 8ball loaded")

    @app_commands.command(name="command_8ball", description="command_8ball")
    @app_commands.rename(query="command_8ball_query")
    @app_commands.describe(query="command_8ball_query")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eightball(self, interaction: discord.Interaction, query: Optional[str]):
        settings = get_data_manager("user", interaction.user.id)

        response = random.choice(responses)

        if not query:
            await interaction.response.send_message(f"🎱 {response}")
            return

        if settings["Global: Compact mode"]:
            await interaction.response.send_message(f"🎱 **{query}** | {response}")
        else:
            await interaction.response.send_message(embed=embed_template(interaction, f"🎱 {query}", f"{response}"))

async def setup(client):
    await client.add_cog(EightBallCog(client))
