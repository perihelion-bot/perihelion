import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

import time

def _get_choices_from_list_settings():
    return [app_commands.Choice(name=x,value=x) for x in get_data_manager("user", 0).get_available_data_keys(bypass_locked=False)]

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class UserSettingsCog(commands.GroupCog, group_name="command_usersettings"):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.language = client.get_cog('language')
        self.last_clear = {}
        
    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: user settings loaded")

    @app_commands.command(name="command_usersettings_set", description="command_usersettings_set")
    @app_commands.rename(setting="command_usersettings_set_setting", value="command_usersettings_set_value")
    @app_commands.describe(setting="command_usersettings_set_setting", value="command_usersettings_set_value")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(setting=_get_choices_from_list_settings())
    async def set(self, interaction: discord.Interaction, setting: app_commands.Choice[str], value: str):
        settings = get_data_manager("user", interaction.user.id)

        setting_val = setting.value
        setting_type = settings.get_data_type(setting_val)
        if setting_type is bool:
            if value.lower() in ["1", "yes", "y", "true", "t", "да", "д", "правда", "tak", "prawda", "p", "evet", "e", "doğru", "d"]:
                value_typed = True
            elif value.lower() in ["0", "no", "n", "false", "f", "нет", "н", "ложь", "nie", "fałsz", "hayır", "h", "yanlış"]:
                value_typed = False
            else:
                await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("usersettings_boolean_check_fail", interaction)), ephemeral=True)
                return
        elif setting_type is str:
            value_typed = value
        else:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("usersettings_type_fail", interaction)), ephemeral=True)
            return
        settings.write_unprivileged(setting_val, value_typed)

        message = self.translator.translate_from_interaction("usersettings_success_details", interaction, [setting.value, value])
        
        if settings["Global: Compact mode"]:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed_template(interaction, self.translator.translate("usersettings_success", interaction), message), ephemeral=True)

    @app_commands.command(name="command_usersettings_get", description="command_usersettings_get")
    @app_commands.rename(setting="command_usersettings_get_setting")
    @app_commands.describe(setting="command_usersettings_get_setting")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(setting=_get_choices_from_list_settings())
    async def get(self, interaction: discord.Interaction, setting: app_commands.Choice[str]):
        setting_val = setting.value
        settings = get_data_manager("user", interaction.user.id)
        
        setting_value = settings[setting_val]
        message = self.translator.translate_from_interaction("usersettings_value_details", interaction, [setting_val, setting_value])

        if settings["Global: Compact mode"]:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed_template(interaction, self.translator.translate("usersettings_value", interaction, [setting_val]), message), ephemeral=True)


    @app_commands.command(name="command_usersettings_clear", description="command_usersettings_clear")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def clear(self, interaction: discord.Interaction):
        settings = get_data_manager("user", interaction.user.id)

        if interaction.user.id not in self.last_clear or self.last_clear[interaction.user.id] + 30 < time.time():
            self.last_clear[interaction.user.id] = time.time()
            message = self.translator.translate_from_interaction("usersettings_confirm_clear", interaction)
            if settings["Global: Compact mode"]:
                await interaction.response.send_message(message, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed_template(interaction, self.translator.translate_from_interaction("usersettings_confirm_clear_title", interaction), message), ephemeral=True)
            return
        
        settings.clear_data(False)
        message = self.translator.translate_from_interaction("usersettings_cleared", interaction)

        if settings["Global: Compact mode"]:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed_template(interaction, self.translator.translate_from_interaction("usersettings_cleared_title", interaction), message), ephemeral=True)


async def setup(client):
    await client.add_cog(UserSettingsCog(client))
