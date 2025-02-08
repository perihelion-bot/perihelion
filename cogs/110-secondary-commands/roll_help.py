import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str


from reactionmenu import ViewMenu, ViewButton

class RollHelpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: roll help loaded")

    @app_commands.command(name="roll_help", description="Help with /roll's syntax.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def roll_help(self, interaction: discord.Interaction):
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        menu.add_page(embed_template(interaction, "Basics", """You can roll a dice by just inputting a number, e.g. `100`, which will roll a dice with that many sides.

However, you may also specify the amount of dice being rolled, like `3d100`. This also works without the amount [so `d100` is the same as `100`].
You can also roll multiple different sets of dice in the same command (like `2d10 3d20`). This is effectively the same as doing two seperate commands for each..

Ranges are also supported, however this does not work without the `d` prefix [which also applies to the rest of this entire document].
You can do something like `d10:100`. Both extremes are also included, so you could roll a 10 or 100.

You can also use underscores, which will get completely removed before parsing (e.g. `1d10_000_000` = `1d10000000`). This is especially useful for large numbers."""))

        menu.add_page(embed_template(interaction, "Modifiers", """You can also add modifiers! These allow you to add to rolls, multiply, etc. Note that modifiers add to all dice rolls, so `2d10+5` will add 10 total, 5 to each roll.

The most basic type is math operations, like +, -, \\*, ^, and /. You can tack them to the end of a roll (like `d100+5*3`) and they will modify the result of the roll (in left-to-right order, no PEMDAS)

There are two other types of modifiers, on the next two pages."""))


        menu.add_page(embed_template(interaction, "Targeted Modifiers", """Then you have the *i* modifier, the most complex one. It lets you choose which rolls will be affected by modifiers. This can best be explained with two examples:
- `3d100i1,3:+20` will roll 3 dice and then add 20 to the first and third.
- `3d100i1,3:+20;2,-5` will do the same, and then subtract 5 from the second.
To put it into actual words, though, the part before the colon is what rolls are selected, and the part after is the list of modifiers. You can do multiple, e.g. *+20\\*3*."""))

        menu.add_page(embed_template(interaction, "Formatting Modifiers", """There are also format modifiers. A complete list is:
- *l* will format the roll into a list.
- *l5* will do the same but split it into groups of 5.
- *s* will only display the sum.
- *==50* will highlight rolls which are exactly 50.
- *>50* will highlight rolls that are at least 50.
- *<50* will highlight rolls that are 50 or lower.
- You can do the last two without a number, in which it will default to the maximum and minimum respectively.
- *top2* will highlight the top 2 rolls.
- *bottom2* will highlight the bottom 2 rolls.
- The two above work the same as > and < respectively, if they don't have a number."""))

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        await menu.start()

async def setup(client):
    await client.add_cog(RollHelpCog(client))
