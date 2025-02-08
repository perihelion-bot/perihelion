import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from utils.roblox_usernames import get_random_username

class UsernameCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.language = client.get_cog('language')

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: username loaded")

    @app_commands.command(name="command_username", description="command_username")
    @app_commands.rename(count="command_username_count")
    @app_commands.describe(count="command_username_count")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def username(self, interaction: discord.Interaction, count: Optional[app_commands.Range[int, 1, 10]]):
        settings = get_data_manager("user", interaction.user.id)
        if count is None:
            count = 1
        if count == 1:      
            title = self.translator.translate_from_interaction("username_generated", interaction)
        else:
            title = self.translator.translate_from_interaction("username_generated_plural", interaction)
        await interaction.response.defer()
        usernames = []
        for i in range(count):
            usernames.append(get_random_username())
        if settings["Global: Compact mode"]:
            await interaction.followup.send(f"{title} | {self.language.list_format(interaction, usernames)}")
        else:
            await interaction.followup.send(embeds=[embed_template(interaction, title,
                                                                "\n".join(usernames))])
async def setup(client):
    await client.add_cog(UsernameCog(client))
