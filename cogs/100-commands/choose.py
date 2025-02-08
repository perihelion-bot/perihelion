import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

import random

class ChooseCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.language = client.get_cog('language')

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: choose loaded")

    @app_commands.command(name="command_choose", description="command_choose")
    @app_commands.describe(options="command_choose_options", count="command_choose_count", unique="command_choose_unique")
    @app_commands.rename(options="command_choose_options", count="command_choose_count", unique="command_choose_unique")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def choose(self, interaction: discord.Interaction, options: str, count: Optional[int], unique: Optional[bool]):
        settings = get_data_manager("user", interaction.user.id)

        if count is None:
            count = 1
        if unique is None:
            unique = True

        option_list = options.split(";")
        option_list = [x.strip() for x in option_list]
        if count > 0:
            if unique:
                if len(option_list) >= count:
                    if settings["Global: Compact mode"]:
                        await interaction.response.send_message(f"{self.language.list_format(interaction, random.sample(option_list, k=count))}")
                    else:
                        await interaction.response.send_message(
                            embed=embed_template(interaction, 
                                                 self.translator.translate_from_interaction("choose_lets_pick", interaction,
                                                                                            [self.language.list_format(interaction, random.sample(option_list, k=count))])))
                else:
                    await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("choose_too_many_choices", interaction)))
            else:
                if settings["Global: Compact mode"]:
                    await interaction.response.send_message(f"{self.language.list_format(interaction, random.choices(option_list, k=count))}")
                else:
                    await interaction.response.send_message(
                        embed=embed_template(interaction,
                                                 self.translator.translate_from_interaction("choose_lets_pick", interaction,
                                                                                            [self.language.list_format(interaction, random.choices(option_list,k=count))])))
        else:
            await interaction.response.send_message(embed=error_template(interaction,  self.translator.translate_from_interaction("choose_zero_choices", interaction)))

async def setup(client):
    await client.add_cog(ChooseCog(client))
