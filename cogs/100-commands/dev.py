import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from utils.checks import developer_only

def _get_choices_from_list_settings():
    return [app_commands.Choice(name=x,value=x) for x in get_data_manager("user", 0).get_available_data_keys(bypass_locked=True)]

class DeveloperCommandsCog(commands.GroupCog, group_name="dev"):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: developer loaded") # This cog left untranslated. It's a developer command.

    @app_commands.command(name="set_usrstg", description="A developer command. You can't run this, maybe you're looking for /usersettings set?")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(setting=_get_choices_from_list_settings())
    @developer_only()
    async def set_usersettings(self, interaction: discord.Interaction, userid: str, setting: app_commands.Choice[str], value: str):
        settings = get_data_manager("user", int(userid))

        setting_val = setting.value
        setting_type = settings.get_data_type(setting_val)
        if setting_type is bool:
            if value.lower() in ["1", "yes", "y", "true", "t"]:
                value_typed = True
            elif value.lower() in ["0", "no", "n", "false", "f"]:
                value_typed = False
            else:
                await interaction.response.send_message(embed=error_template(interaction, "The setting you're trying to set is a boolean, so it must be true or false!"))
                return
        elif setting_type is str:
            value_typed = value
        elif setting_type is int:
            value_typed = int(value)
        elif setting_type is float:
            value_typed = float(value)
        else:
            await interaction.response.send_message(embed=error_template(interaction, "The option can't find the correct typing, don't forget to add it!"))
            return
        settings[setting_val]=value_typed
        await interaction.response.send_message(f"`{userid}`'s {setting_val} set to {value_typed}", ephemeral=True)

    @app_commands.command(name="get_usrstg", description="A developer command. You can't run this, maybe you're looking for /usersettings get?")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(setting=_get_choices_from_list_settings())
    @developer_only()
    async def get_usersettings(self, interaction: discord.Interaction, userid: str, setting: app_commands.Choice[str]):
        settings = get_data_manager("user", int(userid))

        setting_val = setting.value
        settings = get_data_manager("user", interaction.user.id)

        setting_value = settings[setting_val]

        await interaction.response.send_message(f"`{userid}`'s {setting_val} is set to {setting_value}", ephemeral=True)

    @app_commands.command(name="get_allusrstg", description="A developer command. You can't run this.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @developer_only()
    async def get_allusersettings(self, interaction: discord.Interaction, userid: str):
        settings = get_data_manager("user", int(userid))

        await interaction.response.send_message(f"`{userid}`'s settings:\n\n{settings.get_data()}", ephemeral=True)


async def setup(client):
    await client.add_cog(DeveloperCommandsCog(client))
