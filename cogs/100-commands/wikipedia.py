import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from cfg import BOT_NAME, VERSION

import requests

class WikipediaCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: wikipedia loaded")

    @app_commands.command(name="command_wikipedia", description="command_wikipedia")
    @app_commands.rename(query="command_wikipedia_query")
    @app_commands.describe(query="command_wikipedia_query")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def wikipedia(self, interaction: discord.Interaction, query: str):

        url = 'https://en.wikipedia.org/w/rest.php/v1/search/title'
        headers = {
            'User-Agent': f'{BOT_NAME}/{VERSION} (@whirlingstars on Discord)'
        }
        params = {
            'q': query,
            'limit': '1'
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if not data['pages']:
            await interaction.response.send_message(embed=error_template(interaction, f"No search results found for query `{query}`!"))

        url2 = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=true&exlimit=1&titles={data['pages'][0]['key']}&explaintext=1&format=json&formatversion=2"
        response2 = requests.get(url2, headers=headers)
        data2 = response2.json()
        string = data2["query"]["pages"][0]["extract"]
        if len(string) > 200:
            string = string[:200] + "..."
        message = self.translator.translate_from_interaction("wikipedia_message", interaction, [f"https://en.wikipedia.org/wiki/{data['pages'][0]['key']}", string])
        await interaction.response.send_message(embed=embed_template(interaction, f"{data['pages'][0]['title']}", message))

async def setup(client):
    await client.add_cog(WikipediaCog(client))
