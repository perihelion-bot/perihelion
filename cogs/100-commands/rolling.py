import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from rollplayerlib import Format, UnifiedDice, SolveMode, RollException, FormatType
from utils.rolling.coloring import *

class RollCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    # Use @command.Cog.listener() for an event-listener (on_message, on_ready, etc.)
    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: rolling loaded")

    @app_commands.command(name="command_roll", description="command_roll")
    @app_commands.rename(rolls="command_roll_rolls")
    @app_commands.describe(rolls="command_roll_rolls")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def roll(self, interaction: discord.Interaction, rolls: Optional[str]):

        settings = get_data_manager("user", interaction.user.id)

        if not rolls:
            rolls = settings["Rolling: Default roll"]
            assert type(rolls) is str

        rolls.replace("_", "")

        # Split the input string into individual roll expressions
        roll_expressions = rolls.split()

        results = []
        result_mins = []
        result_maxs = []
        formats = []

        # Roll each expression and collect the results
        for roll_expression in roll_expressions:
            try:
                stripped_expression, formatting = Format.parse(roll_expression)
                result = UnifiedDice.new(stripped_expression).solve(SolveMode.RANDOM)
                result_min = UnifiedDice.new(stripped_expression).solve(SolveMode.MIN)
                result_max = UnifiedDice.new(stripped_expression).solve(SolveMode.MAX)
                formats.append(formatting)
                results.append(result)
                result_mins.append(result_min)
                result_maxs.append(result_max)
            except RollException as exc:
                await interaction.response.send_message(embed=error_template(interaction, exc.information))
                return

        if settings["Global: Compact mode"]:
            message = ""
            for i, result in enumerate(results):
                try:
                    for tup in result.format(formats[i]):
                        message = message + f"**{result.roll_string}** | {tup[1]}\n"
                        if len(message) > 2000:
                            raise RollException("Roll result too long.")
                except RollException:
                    embed = error_template(interaction, self.translator.translate_from_interaction("roll_result_too_long", interaction))
                    break
            await interaction.response.send_message(message)
            return
        else:
            embed = embed_template(interaction, f"--- {' '.join(roll_expressions)} ---")

            normalized_results = [normalize(sum(mini.rolls), sum(maxi.rolls), sum(result.rolls)) for mini, maxi, result in
                                  zip(result_mins, result_maxs, results)]
            normalized_color_value = sum(normalized_results) / len(normalized_results)

            embed.color = color_hsv(normalized_color_value)

            for i, result in enumerate(results):
                try:
                    for tup in result.format(formats[i]):
                        if len(tup[1]) > 1024:
                            raise RollException("Roll result too long.")
                        embed.add_field(name=f"{tup[0]}", value=tup[1], inline=False)
                except RollException:
                    embed = error_template(interaction, self.translator.translate_from_interaction("roll_result_too_long", interaction))
                    break
            await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(RollCog(client))
