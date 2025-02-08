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
import sys
from typing import List
import traceback

class WriteTextModal(discord.ui.Modal):
    def __init__(self, wmcog, wikimanager, original_interaction):
        self.wmcog = wmcog
        self.wikimanager = wikimanager
        self.interaction = original_interaction
        self.locale = self.interaction.locale
        self.translator = wmcog.client.tree.translator
        page_title = self.translator.translate_sync("notes_creation_title", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))
        tr_title_lb = self.translator.translate_sync("notes_title_label", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))
        tr_title_pl = self.translator.translate_sync("notes_title_placeholder", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))
        tr_cnt_lb = self.translator.translate_sync("notes_content_label", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))
        tr_cnt_pl = self.translator.translate_sync("notes_content_placeholder", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))

        self.wikipage_title = discord.ui.TextInput(
            label=tr_title_lb,
            style=discord.TextStyle.short,
            placeholder=tr_title_pl,
            max_length=100,
            required=True
        )

        self.wikipage_contents = discord.ui.TextInput(
            label=tr_cnt_lb,
            style=discord.TextStyle.long,
            placeholder=tr_cnt_pl,
            max_length=1800,
            required=True
        )
        super().__init__(title=page_title)
        self.add_item(self.wikipage_title).add_item(self.wikipage_contents)


    async def on_submit(self, interaction: discord.Interaction):
        page_contents = self.wikipage_contents.value
        page_name = self.wikipage_title.value
        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
        try:
            wiki.write_page(page_name, page_contents)
        except ValueError:
            await interaction.response.send_message(embed=error_template(interaction, await self.translator.translate("notes_locked_message", self.locale, discord.app_commands.TranslationContext(discord.app_commands.TranslationContextLocation.other, None))), ephemeral=True)
        self.wikimanager.save_wiki(wiki)
        await interaction.response.send_message(await self.translator.translate(
            "notes_edited_message",
            self.locale,
            discord.app_commands.TranslationContext(
                discord.app_commands.TranslationContextLocation.other,
                [page_name, page_contents]
            ))
            , ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'```py\n{''.join(traceback.format_exception(error)).replace("\\n", "\n")}```', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class NoteCog(commands.GroupCog, group_name="command_note"):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator
        self.wmcog = client.get_cog('wikimanager')
        self.wikimanager = self.wmcog.WikiManager()

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: notes loaded")

    @app_commands.command(name="command_note_create", description="command_note_create")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(WriteTextModal(self.wmcog, self.wikimanager, interaction))

    @app_commands.command(name="command_note_edit", description="command_note_edit")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def edit(self, interaction: discord.Interaction):
        await interaction.response.send_modal(WriteTextModal(self.wmcog, self.wikimanager, interaction))

    @app_commands.command(name="command_note_read", description="command_note_read")
    @app_commands.rename(page="command_note_read_page")
    @app_commands.describe(page="command_note_read_page")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def read(self, interaction: discord.Interaction, page: str):
        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
        try:
            page_content = wiki.read_page(page)
        except ValueError:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("wiki_note_not_found", interaction)), ephemeral=True)
            return
        await interaction.response.send_message(embed=embed_template(interaction, page, page_content))

    @app_commands.command(name="command_note_lock", description="command_note_lock")
    @app_commands.rename(page="command_note_lock_page")
    @app_commands.describe(page="command_note_lock_page")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lock(self, interaction: discord.Interaction, page: str):
        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
        try:
            wiki.lock_page(page)
            self.wikimanager.save_wiki(wiki)
        except ValueError:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("wiki_note_not_found", interaction)), ephemeral=True)
        await interaction.response.send_message(embed=success_template(interaction, f"{page} locked"))

    @app_commands.command(name="command_note_delete", description="command_note_delete")
    @app_commands.rename(page="command_note_delete_page")
    @app_commands.describe(page="command_note_delete_page")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def delete(self, interaction: discord.Interaction, page: str):
        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
        try:
            wiki.delete_page(page)
            self.wikimanager.save_wiki(wiki)
        except ValueError:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("wiki_note_not_found", interaction)), ephemeral=True)
        await interaction.response.send_message(embed=success_template(interaction, f"{page} wiped"))

    @app_commands.command(name="command_note_unlock", description="command_note_unlock")
    @app_commands.rename(page="command_note_unlock_page")
    @app_commands.describe(page="command_note_unlock_page")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unlock(self, interaction: discord.Interaction, page: str):

        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
        try:
            wiki.unlock_page(page)
            self.wikimanager.save_wiki(wiki)
        except ValueError:
            await interaction.response.send_message(embed=error_template(interaction, self.translator.translate_from_interaction("wiki_note_not_found", interaction)), ephemeral=True)
        await interaction.response.send_message(embed=success_template(interaction, f"{page} unlocked"))

#    @app_commands.command(name="list")
#    @app_commands.allowed_installs(guilds=True, users=True)
#    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
#    async def list(self, interaction: discord.Interaction):
#        """
#        List out all notes.
#        """
#        wiki, _ = self.wikimanager.get_or_create_wiki(interaction.user.id, f"{interaction.user.name}'s notes")
#        await viewmenu_paginate_entries(interaction, wiki.get_all_page_titles(), "Your notes")


# The `setup` function is required for the cog to work
# Don't change anything in this function, except for the
# name of the cog to the name of your class.
async def setup(client):
    await client.add_cog(NoteCog(client))
