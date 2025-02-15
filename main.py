import random
from typing import Any
import discord, asyncio, sys, os, traceback
from discord.abc import PrivateChannel
from discord.app_commands.errors import AppCommandError, CommandInvokeError
from discord.ext import commands
from cfg import TOKEN, PRESENCE, VERSION, SYNCING, BOT_NAME, ERROR_LOGGING_CHANNEL, DONT_LOAD_COGS
from utils.logging import log
from utils.embeds import error_template, embed_template
from pathlib import Path
from utils.translation import JSONTranslator
from assets.errors.errormsgs import messages
import string

class Perihelion(commands.Bot):
    coglist = []
    error_channel: Any = None
    

    async def setup_hook(self) -> None:
        await bot.tree.set_translator(JSONTranslator())
        cogs_dir = Path('cogs')
        priority_folders = sorted(
            [d for d in cogs_dir.iterdir() if d.is_dir() and d.name.split("-", 1)[0].isdigit()],
            key=lambda x: int(x.name.split("-", 1)[0])
        )

        for priority_folder in priority_folders:
            log.debug(f"Loading cogs from priority folder: {priority_folder.name}")
            cog_files = [f for f in priority_folder.glob('*.py') if f.is_file()]

            for cog_file in cog_files:
                cog_name = f"cogs.{priority_folder.name}.{cog_file.stem}"
                if cog_name in DONT_LOAD_COGS:
                    log.debug(f"NOT loading extension {cog_name}")
                    continue
                log.debug(f"Loading extension {cog_name}")
                try:
                    await self.load_extension(cog_name)
                    self.coglist.append(cog_name)
                    log.debug(f"Extension {cog_name} loaded")
                except Exception as e:
                    log.error(f"Failed to load extension {cog_name}: {e}")
                    print(traceback.print_exc())

            log.debug(f"Cogs: {self.coglist}")

        if SYNCING['SHOULD_SYNC']:
            log.info(f"Syncing commands to guild {SYNCING['SERVER']}")
            await self.tree.sync(guild=self.get_guild(SYNCING['SERVER']))
        else:
            log.info("Not syncing commands.")



intents = discord.Intents.default()

bot = Perihelion(intents=intents, command_prefix="r!")  # Setting prefix

def generate_base36_string(length=8):
    base36_chars = string.digits + string.ascii_lowercase  # More readable and standard
    result_string = ''.join(random.choice(base36_chars) for _ in range(length)) # More concise using random.choice and join
    return result_string

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: AppCommandError):
    message = random.choice(messages)
    errorcode = generate_base36_string(8)
    if not bot.error_channel:
        bot.error_channel = bot.get_channel(ERROR_LOGGING_CHANNEL)
    command = interaction.command
    if command is not None:
        log.warning(f'Exception occured in command/contextmenu {command.name} by user {interaction.user.name}', exc_info=error)
    else:
        log.warning(f'Exception occured by user {interaction.user.name}', exc_info=error)

    if isinstance(error, CommandInvokeError):
        await interaction.response.send_message(embed=error_template(interaction, f"### {type(error.original).__name__}\n\n{message}\n\n```{error.original}```\n-# If you're reporting an issue, send this along: {errorcode}"), ephemeral=True)
        await bot.error_channel.send(embed = embed_template(interaction, "error logging", f"## Exception occured in command/contextmenu {command.name if command else "non-command"} by user {interaction.user.name}\n\n ### {type(error.original).__name__}\n\n```{"".join(traceback.format_exception(error.original)).replace("\\n", "\n")}```\n-# errorcode: {errorcode}")) #pyright: ignore[reportCallIssue, reportOptionalMemberAccess, reportAttributeAccessIssue]
        return
    await interaction.response.send_message(embed=error_template(interaction, f"### {type(error).__name__}\n\n{message}\n\n```{error.args[0]}```\n-# If you're reporting an issue, send this along: {errorcode}"), ephemeral=True)
    await bot.error_channel.send(embed = embed_template(interaction, "error logging", f"## Exception occured in command/contextmenu {command.name if command else "non-command"} by user {interaction.user.name}\n\n ### {type(error).__name__}\n\n```{"".join(traceback.format_exception(error)).replace("\\n", "\n")}```\n-# errorcode: {errorcode}")) #pyright: ignore[reportCallIssue, reportOptionalMemberAccess, reportAttributeAccessIssue]


@bot.event
async def on_ready():
    log.info(f"{BOT_NAME} online.")
    log.info(f"servers | {len(bot.guilds)}")
    log.info(f"version | {VERSION}")
    log.info(f"cogs    | {len(bot.coglist)} (and {len(DONT_LOAD_COGS)} in blacklist)")
    log.debug(f"Logged in as {bot.user}.")
    await bot.change_presence(activity=discord.Game(name=PRESENCE))

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        log.critical("token invalid")
        sys.exit()
    except Exception as err:
        log.critical(f"error: {err}")
        sys.exit()
