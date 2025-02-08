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

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class RstCog(commands.GroupCog, group_name="command_rst"):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.filename = "./data/custom_texts.txt"
        self.modqueue = "./data/custom_text_queued.txt"

        # Ensure the file exists
        try:
            with open(self.filename, 'a'):
                pass
        except IOError as e:
            log.error(f"Error creating or accessing the file: {e}")

    def add_text(self, text):
        try:
            with open(self.modqueue, 'a') as file:
                file.write(text + '\n')
        except IOError as e:
            log.error(f"Error writing to modqueue: {e}")

    def get_random_text(self):
        try:
            with open(self.filename, 'r') as file:
                texts = file.readlines()
            return random.choice(texts).strip() if texts else "[No texts in database]"
        except IOError as e:
            log.error(f"Error reading from file: {e}")
            return "[Error reading from database]"

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: rst loaded")

    @app_commands.command(name="command_rst_add", description="command_rst_add")
    @app_commands.rename(text="command_rst_add_text")
    @app_commands.describe(text="command_rst_add_text")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def add(self, interaction: discord.Interaction, text: str):
        self.add_text(text)
        settings = get_data_manager("user", interaction.user.id)

        if settings["Global: Compact mode"]:
            await interaction.response.send_message(self.translator.translate_from_interaction("rst_text_added_content", interaction))
        else:
            await interaction.response.send_message(embeds=[embed_template(interaction, self.translator.translate_from_interaction("rst_text_added_title", interaction),
                                                                           self.translator.translate_from_interaction("rst_text_added_content", interaction))])

    @app_commands.command(name="command_rst_get", description="command_rst_get")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get(self, interaction: discord.Interaction):
        settings = get_data_manager("user", interaction.user.id)
        text = self.get_random_text()
        if settings["Global: Compact mode"]:
            await interaction.response.send_message(text)
        else:
            await interaction.response.send_message(embed=embed_template(interaction, self.translator.translate_from_interaction("rst_random_text_title", interaction), text))

async def setup(client):
    await client.add_cog(RstCog(client))
