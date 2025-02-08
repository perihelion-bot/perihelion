import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class GamesCog(commands.GroupCog, group_name="command_game"):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.ttt = client.get_cog('games/tictactoe')

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: games loaded")

    @app_commands.command(name="command_game_tictactoe", description="command_game_tictactoe")
    @app_commands.describe(size="command_game_tictactoe_size", row="command_game_tictactoe_row", misere="command_game_tictactoe_misere")
    @app_commands.rename(size="command_game_tictactoe_size", row="command_game_tictactoe_row", misere="command_game_tictactoe_misere")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def tictactoe(self, interaction: discord.Interaction, size: Optional[app_commands.Range[int, 3, 5]], row: Optional[app_commands.Range[int, 3, 5]], misere: Optional[bool] = False):
        if size is None:
            size = 3
        if row is None:
            row = size #its probably expected that the row length = the size
        if row > size:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("tictactoe_row_oversize", interaction)), ephemeral=True)
        else: # Next string intentionally left untranslated. This is because it could be used between people of different languages.
            await interaction.response.send_message(f"Pick a place to start! {"Note that this game is in misere mode, so your goal is to lose!"}", view=self.ttt.TicTacToe(size, row, misere))

async def setup(client):
    await client.add_cog(GamesCog(client))
