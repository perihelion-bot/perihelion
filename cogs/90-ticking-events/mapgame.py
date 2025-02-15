if __name__ == "__main__":
    from os import getcwd, chdir
    from sys import path
    chdir("../..")
    path.append(getcwd())

import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

import colorsys
import random
from cfg import VERSION, MAPGAME
from PIL import Image
import pickle
from discord.ext import tasks

from utils.mapgame.core import Tile, Country, MapGameInstance

class MapGameCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator
        self.channel = client.get_channel(MAPGAME["CHANNEL"])
        try:
            with open("data/mapgame.pickle", "rb") as f:
                self.instance: MapGameInstance = pickle.load(f)
        except FileNotFoundError:
            log.error("Mapgame pickle file not found, bail!")
            raise FileNotFoundError("mapgame.pickle file not found.")


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: mapgame loaded")

    #@tasks.loop(seconds=MAPGAME["STEPRATE"])
    async def mapgame_step_loop(self):
        if MAPGAME["ENABLED"]:
            await self.instance.mapgame_step()

    @app_commands.command(name="command_mapgame", description="command_mapgame")
    @app_commands.rename(arg1="command_mapgame_arg1")
    @app_commands.describe(arg1="command_mapgame_arg1")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def mapgame(self, interaction: discord.Interaction, arg1: Optional[app_commands.Range[int, 1, 10]]):
        settings = get_data_manager("user", interaction.user.id)
        await interaction.response.defer()
        await self.instance.mapgame_step()
        await interaction.followup.send(file=await self.instance.render()) 

async def setup(client):
    await client.add_cog(MapGameCog(client))
    
if __name__ == "__main__":
    print(f"mapgame curation script [perihelion version: {VERSION}]")
    print("-"*50)
    print(f"1: generate base map pickle")
    print(f"2: analyze pickle")
    print(f"3: create country list dictionary")
    print(f"4: generate random country name")
    num = input("put in a number: ")
    if num not in ["1", "2", "3", "4"]:
        print(f"thats not an option")
    if num == "1":
        image = Image.open("assets/mapgame/map.png")
        instance = MapGameInstance.parse_image(image)
        for i in range(10):
            tile = instance.random_available_tile()
            country_color = colorsys.hsv_to_rgb(random.random(), (random.random()/2)+0.5, (random.random()/2)+0.5)
            country_color = tuple(int(clr*255) for clr in country_color)
            country_id = instance.countries.append(Country(instance.CountryNamer().generate(), {}, -1, 5, 0, 0, 1, country_color, 0))
            tile.owner_id = country_id
            instance.border_tiles.append(tile)
        with open("data/mapgame.pickle", "wb") as f:
            pickle.dump(instance, f)
    if num == "2":
        with open("data/mapgame.pickle", "rb") as f:
            instance = pickle.load(f)
        raise Exception
    if num == "3":
        names = []
        with open("assets/mapgame/countrynames.txt", "r") as f:
            txt = f.read()
            names = txt.split("\n")

        frequency_dict = {"START": {}}  # Initialize with "START" key

        for name in names:
            if not name:  # Handle empty names if needed
                continue

            first_letter = name[0]
            if first_letter not in frequency_dict["START"]:
                frequency_dict["START"][first_letter] = 0
            frequency_dict["START"][first_letter] += 1

            for i in range(len(name) - 1): # Iterate up to the second to last letter
                current_letter = name[i]
                next_letter = name[i+1]# Adding a new country
                if current_letter not in frequency_dict:
                    frequency_dict[current_letter] = {} # Initialize if not present

                if next_letter not in frequency_dict[current_letter]:
                    frequency_dict[current_letter][next_letter] = 0
                frequency_dict[current_letter][next_letter] += 1

            last_letter = name[-1]
            if last_letter not in frequency_dict:
                frequency_dict[last_letter] = {} # Initialize if not present
            frequency_dict[last_letter]["END"] = frequency_dict[last_letter].get("END", 0) + 1 # Increment "END" count

        print(repr(frequency_dict))
    if num == "4":
        namerinst = MapGameInstance([[]], [], [], 0)
        namer = namerinst.CountryNamer()
        for i in range(10):
            print(namer.generate())