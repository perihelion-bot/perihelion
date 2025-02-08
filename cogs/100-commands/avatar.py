import discord
from discord import app_commands, User, AppCommandContext
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager

from PIL import Image
from utils.image import crop_circle
from io import BytesIO

class AvatarCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

        self.ctx_menu = app_commands.ContextMenu(
            name='command_avatar_ctxmenu',
            callback=self.avatar_menu,
        )
        self.client.tree.add_command(self.ctx_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: avatar loaded")

    @staticmethod
    async def get_avatar(user: User, crop=False):
        avatar = await user.display_avatar.read()
        img = Image.open(BytesIO(avatar))
        if crop: img = crop_circle(img)

        #send
        b = BytesIO()
        img.save(b, "PNG")
        b.seek(0)
        return b

    @app_commands.command(name="command_avatar", description="command_avatar")
    @app_commands.describe(user="command_avatar_user", crop="command_avatar_crop")
    @app_commands.rename(user="command_avatar_user", crop="command_avatar_crop")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, interaction: discord.Interaction, user: User, crop: bool = False):
        avatar = await self.get_avatar(user, crop)
        await interaction.response.send_message(file=discord.File(avatar,"image.png"))

    async def avatar_menu(self, interaction: discord.Interaction, user: User):
        avatar = await self.get_avatar(user)
        await interaction.response.send_message(file=discord.File(avatar,"image.png"))

async def setup(client):
    await client.add_cog(AvatarCog(client))
