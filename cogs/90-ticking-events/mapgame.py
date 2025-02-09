import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from cfg import VERSION, MAPGAME
from PIL import Image
from dataclasses import dataclass
from enum import IntFlag, Enum
import pickle
from discord.ext import tasks
import random

import timeit

@dataclass
class Tile:
    class TileFlags(IntFlag):
        WATER = 0
        LAND = 1
        CROSSABLE = 2
        
    flags: TileFlags
    coordinates: tuple[int, int]
    income: int
    owner_id: int

@dataclass
class Country:
    class Relations(Enum):
        ALLIED = 2
        FRIENDLY = 1
        NEUTRAL = 0
        ENEMIES = -1
        WAR = -2
    
    name: str
    relations: dict[int, Relations]
    id: int
    strength: int
    money: int
    income: int

@dataclass
class MapGameInstance:
    tiles: list[list[Tile]]
    border_tiles: list[Tile]
    _countries: list[Country]
    turn: int
    
    @staticmethod
    def parse_image(img: Image):
        width, height = img.size
        tiles = []
        for x in range(width):
            tiles.append([])
            print(f"row {x+1}/{width} parsing")
            for y in range(height):
                _r, g, b, _a = img.getpixel((x, y))
                match b:
                    case 255:
                        flags = Tile.TileFlags.WATER
                    case 128:
                        flags = Tile.TileFlags.CROSSABLE
                    case 0:
                        flags = Tile.TileFlags.LAND | Tile.TileFlags.CROSSABLE
                income = g >> 4
                tiles[x].append(Tile(flags, (x, y), income, 0))
        return MapGameInstance(tiles, [], [], 0)
    
    class CountryAccessor: # Helper class to handle country access in a way that makes sense (e.g. not instance[2])
        def __init__(self, countries_list: list[Country]):
            self._countries_list = countries_list

        def __getitem__(self, country_id: int) -> Country:
            for country in self._countries_list:
                if country.id == country_id:
                    return country
            raise KeyError(f"Country with id {country_id} not found.")

        def __setitem__(self, country_id: int, country: Country):
            if not isinstance(country, Country):
                raise TypeError("Value must be a Country object.")
            found = False
            replaced_index = -1
            for i, existing_country in enumerate(self._countries_list):
                if existing_country.id == country_id:
                    self._countries_list[i] = country
                    found = True
                    replaced_index = i
                    break

            if not found:
                self._countries_list.append(country)
                # Initialize relations for the new country and all existing countries
                for c in self._countries_list:
                    if c.id != country.id:
                        if country.id not in c.relations:
                            c.relations[country.id] = Country.Relations.NEUTRAL
                        if c.id not in country.relations:
                            country.relations[c.id] = Country.Relations.NEUTRAL


        def __delitem__(self, country_id: int):
            for i, country in enumerate(self._countries_list):
                if country.id == country_id:
                    del self._countries_list[i]
                    return
            raise KeyError(f"Country with id {country_id} not found.")
        
        def append(self, country: Country) -> int:
            if not isinstance(country, Country):
                raise TypeError("Value must be a Country object.")

            existing_ids = {c.id for c in self._countries_list}
            new_id = 1
            while new_id in existing_ids:
                new_id += 1
            country.id = new_id

            self._countries_list.append(country)

            for c in self._countries_list:
                if c.id != country.id:
                    if country.id not in c.relations:
                        c.relations[country.id] = Country.Relations.NEUTRAL
                    if c.id not in country.relations:
                        country.relations[c.id] = Country.Relations.NEUTRAL
            return new_id

    @property
    def countries(self):
        return MapGameInstance.CountryAccessor(self._countries)
    
    def random_available_tile(self) -> Tile | None:
        """
            WARNING: this function takes ~50ms! 
        """
        available_tiles = []
        for row in self.tiles:
            for tile in row:
                if Tile.TileFlags.LAND | Tile.TileFlags.CROSSABLE in tile.flags and tile.owner_id == 0:
                    available_tiles.append(tile)
        if available_tiles:
            return random.choice(available_tiles)
        else:
            return None
    
    def all_tiles_country(self, id: int) -> list[Tile] | None:
        """
            WARNING: this function takes ~50ms! 
        """
        available_tiles = []
        for row in self.tiles:
            for tile in row:
                if tile.owner_id == id:
                    available_tiles.append(tile)
        return available_tiles
    
class MapGameCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator
        self.channel = client.get_channel(MAPGAME["CHANNEL"])

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: mapgame loaded")
    
    #@tasks.loop(seconds=MAPGAME["STEPRATE"])
    async def mapgame_step_loop(self):
        if MAPGAME["ENABLED"]:
            await self.mapgame_step()
    
    async def mapgame_step(self):
        ...
        
    @app_commands.command(name="command_mapgame", description="command_mapgame")
    @app_commands.rename(arg1="command_mapgame_arg1")
    @app_commands.describe(arg1="command_mapgame_arg1")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def mapgame(self, interaction: discord.Interaction, arg1: Optional[app_commands.Range[int, 1, 10]]):
        settings = get_data_manager("user", interaction.user.id)
        self.mapgame_step()
        
async def setup(client):
    await client.add_cog(MapGameCog(client))

if __name__ == "__main__":
    print(f"mapgame curation script [perihelion version: {VERSION}]")
    print("-"*50)
    print(f"1: generate base map pickle")
    print(f"2: analyze pickle")
    num = input("put in a number: ")
    if num not in ["1", "2"]:
        print(f"thats not an option")
    if num == "1":
        image = Image.open("assets/mapgame/map.png")
        instance = MapGameInstance.parse_image(image)
        cs1 = instance.random_available_tile()
        cs2 = instance.random_available_tile()
        id1 = instance.countries.append(Country("Test Country 1", {}, -1, 0, 0, 1))
        id2 = instance.countries.append(Country("Test Country 2", {}, -1, 0, 0, 1))
        cs1.owner_id = id1
        cs2.owner_id = id2
        #with open("data/mapgame.pickle", "wb") as f:
        #    pickle.dump(instance, f)
    if num == "2":
        ...