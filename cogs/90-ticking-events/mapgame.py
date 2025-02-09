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
import re

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
    
    class CountryNamer:
        def __init__(self):
            self.weights = {'START': {'a': 76, 'b': 95, 'c': 96, 'd': 36, 'e': 29, 'f': 28, 'g': 56, 'h': 37, 'i': 38, 'j': 24, 'k': 61, 'l': 48, 'm': 93, 'n': 40, 'o': 10, 'p': 71, 'q': 3, 'r': 39, 's': 99, 't': 69, 'u': 27, 'v': 22, 'y': 11, 'z': 11, 'w': 22, "'": 2, 'x': 1, ' ': 1}, 'a': {'f': 17, 'n': 403, 'l': 152, 'END': 327, ' ': 39, 'r': 153, 'u': 48, 'z': 18, 'i': 60, 'h': 19, 'm': 47, 's': 56, 'd': 42, 'b': 36, 't': 123, '-': 7, 'q': 4, 'e': 2, 'p': 15, 'k': 38, 'o': 5, 'g': 22, 'w': 11, 'y': 18, 'c': 18, 'j': 10, 'a': 10, 'v': 24, "'": 2, 'x': 9}, 'f': {'g': 2, 'a': 12, 'r': 15, 'i': 9, ' ': 1, 'END': 3, 'u': 7, 's': 2, 'f': 2, '-': 1, 'e': 24, 'o': 6, 'l': 4}, 'g': {'h': 16, 'e': 39, 'o': 31, 'u': 26, 'l': 6, 'i': 11, 'a': 60, 'y': 4, 'r': 31, 'END': 28, 'd': 1, 'g': 3, 'w': 3, 'b': 1, 'c': 1, 't': 1, 'n': 3, 'z': 1, 'x': 2, ' ': 5, 'k': 2, 'm': 1, '-': 8}, 'h': {'a': 76, 'r': 6, 'END': 20, 'u': 27, 'e': 36, 'i': 47, 'o': 33, 's': 2, 't': 4, ' ': 21, 'l': 3, 'd': 2, 'y': 4, 'w': 6, 'n': 2, 'b': 1, '-': 1, 'c': 1, 'k': 2}, 'n': {'i': 120, 'END': 142, 'd': 98, 'g': 81, 't': 46, 'a': 106, 'e': 78, ' ': 87, 'm': 3, 'l': 6, 'c': 24, 'y': 12, 'o': 39, 's': 18, 'k': 11, 'z': 8, 'u': 5, 'n': 8, 'j': 4, 'r': 1, 'f': 11, '-': 5, 'p': 1, 'h': 2, 'b': 8, 'w': 2}, 'i': {'s': 78, 'a': 250, 'g': 11, 'n': 135, 'j': 6, 'u': 4, 'z': 4, 'v': 21, 'l': 32, 'END': 62, 'c': 62, 'r': 33, 'b': 14, 't': 55, 'o': 27, 'e': 55, 'q': 3, 'p': 21, ' ': 20, 'w': 1, 'k': 13, 'm': 25, 'd': 20, 'f': 3, 'y': 8, '-': 3, 'h': 2, 'x': 2, "'": 1, 'i': 1}, 's': {'t': 95, 'END': 68, 'h': 41, 'n': 4, 'w': 10, 'o': 82, 'a': 56, 's': 32, 'i': 60, 'r': 4, 'c': 13, 'l': 19, ' ': 28, 'e': 28, 'u': 16, 'p': 10, 'y': 9, 'k': 11, '-': 1, 'm': 1, 'z': 1, 'v': 2}, 't': {'a': 94, 'i': 69, 'r': 46, 's': 13, 'e': 82, 'END': 59, 'o': 55, 'h': 34, 'v': 3, 'u': 32, ' ': 60, 't': 12, 'z': 2, 'y': 10, 'n': 5, 'l': 5, 'w': 1, 'm': 1, 'k': 1, '-': 1, 'c': 1}, 'l': {'b': 8, 'g': 13, 'a': 101, 'i': 110, 'END': 25, ' ': 21, 'e': 61, 'o': 43, 'v': 7, 'y': 8, 'u': 23, 'd': 11, 't': 9, 'l': 22, 'k': 3, 'w': 1, '-': 2, 'h': 3, 'm': 4, 's': 3, 'f': 1, 'z': 1, 'p': 2}, 'b': {'a': 78, 'u': 42, 'e': 31, 'h': 1, 'o': 32, 'r': 14, 'l': 6, 'i': 25, 'y': 4, ' ': 3, 'w': 3, 'END': 5, 'b': 1, 'd': 1, 'k': 1}, 'e': {'r': 127, 'n': 110, 's': 61, 'l': 44, 'END': 104, 'g': 21, 'i': 15, 'p': 10, ' ': 39, 'c': 25, 'q': 2, 'a': 41, 't': 63, 'o': 26, 'e': 9, 'm': 25, 'b': 6, 'x': 8, 'w': 8, 'd': 35, 'v': 10, 'y': 5, 'k': 5, 'z': 6, 'j': 6, 'u': 7, "'": 17, 'f': 1, '-': 15, 'h': 1}, 'r': {'i': 108, 'r': 9, 'a': 175, 'b': 10, 'g': 30, 'm': 27, 'u': 44, 'z': 8, 'k': 9, 'd': 18, 'o': 56, 'e': 70, 'END': 40, 'y': 17, 's': 13, 'l': 7, 't': 18, 'w': 6, '-': 3, 'f': 1, 'n': 14, ' ': 16, 'h': 6, 'c': 7, 'q': 1, 'p': 2, 'v': 1}, 'd': {'o': 29, ' ': 24, 'a': 54, 'e': 77, 'i': 34, 'END': 54, "'": 1, 'j': 1, 'u': 8, 's': 10, 'r': 2, 'z': 2, 'h': 3, 'd': 2, 'y': 4, 'b': 1, 't': 1, 'm': 1, 'n': 2, 'l': 1}, 'o': {'r': 81, 'l': 56, 's': 34, 'v': 60, 't': 21, 'END': 51, ' ': 11, 'd': 18, 'o': 3, 'n': 123, 'm': 62, 'i': 10, 'a': 10, 'u': 36, 'p': 25, 'c': 39, 'z': 5, 'g': 14, 'b': 8, 'f': 1, 'k': 5, 'y': 6, 'w': 11, 'q': 2, 'h': 4, '-': 5, 'j': 1}, 'u': {'a': 35, 'd': 8, 's': 55, 'm': 10, 't': 36, 'n': 56, 'l': 20, 'r': 68, 'b': 11, 'i': 17, 'END': 33, 'y': 1, 'w': 4, 'x': 1, 'e': 7, 'g': 11, 'c': 11, 'v': 5, 'k': 21, 'z': 2, '-': 5, 'p': 13, ' ': 2, 'j': 2, 'o': 2, 'h': 2, "'": 1}, ' ': {'a': 53, 'b': 12, 'h': 13, 'f': 16, 'v': 6, 'r': 16, 'd': 13, 's': 83, 'g': 16, 'i': 14, 'z': 2, 'k': 27, 'm': 19, 'n': 11, 'l': 14, 't': 16, 'p': 28, 'e': 8, 'o': 4, 'c': 27, 'END': 21, 'y': 6, 'j': 3, 'q': 2, 'u': 4, 'w': 1, ' ': 1}, 'm': {'e': 48, 'a': 125, 'END': 17, 'b': 23, 'o': 57, 'i': 23, 'y': 6, 'l': 1, 'c': 1, 'm': 12, 'u': 10, 't': 4, ' ': 4, 'p': 4, 'r': 1, 'k': 1}, 'z': {'e': 17, 'i': 14, 'a': 21, 's': 1, 'b': 5, 'u': 6, 'END': 4, 'v': 1, 'm': 1, 'h': 3, 'o': 4, 'c': 1, ' ': 1, 't': 1}, 'j': {'a': 22, 'i': 11, 'o': 7, 'u': 10, 'e': 3, 'd': 3, 'END': 1}, 'v': {'i': 73, 'e': 26, 'o': 22, 'a': 36, 's': 1, 'END': 3, 'g': 1, 'l': 1, 'y': 1}, 'w': {'a': 42, 'i': 7, ' ': 6, 'e': 21, 'o': 3, 'h': 1, 'END': 6, 'u': 1, 'y': 2, 'r': 1, 'n': 3, 'f': 1}, 'k': {'i': 17, 'END': 18, 'a': 54, 'h': 40, 'e': 13, 'o': 27, 'u': 18, 'y': 4, 'm': 2, 'r': 14, 'n': 1, 'w': 2, ' ': 11, 'k': 2, '-': 1, 'f': 2, 'l': 2}, 'c': {'a': 66, 'e': 29, 'END': 13, 'h': 55, 'o': 60, 'r': 21, 'u': 5, 'y': 5, 'z': 7, 'c': 5, 'i': 47, ' ': 8, 't': 4, 'k': 8, 'l': 2, 'n': 1}, 'p': {'u': 11, 'r': 23, 't': 4, 'i': 16, 'a': 41, 'e': 42, 'h': 7, 'p': 11, 'o': 32, 'l': 20, 'g': 1, ' ': 7, 'END': 2, 's': 2}, "'": {'i': 2, 'a': 1, 's': 17, 'd': 1, 'k': 2, 'u': 1}, 'y': {'p': 4, 'END': 34, 'a': 33, 'r': 8, 'z': 2, 's': 3, 'c': 2, 'e': 7, ' ': 19, 't': 2, 'u': 10, 'o': 4, 'i': 2, 'd': 2, 'l': 6, 'f': 1, '-': 1, 'n': 3, 'k': 2}, 'q': {'u': 8, 'END': 3, 'a': 2, 'i': 2, ' ': 1, 'o': 1}, '-': {'b': 7, 'l': 5, 'e': 2, 'r': 3, 'f': 3, 'm': 3, 'p': 2, 'k': 3, 'u': 3, 't': 2, 'n': 2, 'c': 2, 'g': 2, 'h': 4, 's': 8, 'a': 3, 'w': 2, 'v': 2, 'o': 1}, 'x': {'e': 8, 'i': 10, 'END': 2, 'o': 1, 'a': 2}}
            self.min_length = 4
            self.max_length = 24
            self.ending_mult = [0, 0, 0, 0, 0.2, 0.3, 0.5, 0.7, 1, 1.2, 1.6, 2, 2.5, 3, 3.5, 4, 5, 7, 20, 999, 999, 999, 999, 999]
            
        def generate_base(self):
            word = "" #start with the initial word
            last_letter = "START"
            while True:
                picks = list(self.weights[last_letter].keys()) #possible next letters
                pick_weights = list(self.weights[last_letter].values()) #chance for each next letter
                try:
                    pick_weights[picks.index("END")] *= self.ending_mult[len(word)]
                except ValueError: # we can fail if it's not in the list
                    pass
                if len(picks) == 0: #we have reached a letter that never gets followed (shouldn't be necessary in most cases but whatever)
                    break
                genned = random.choices(picks, weights=pick_weights)[0] #add letter
                if genned != "END":
                    word += genned
                else:
                    if len(word) >= self.min_length: 
                        break
                if len(word) >= self.max_length:
                    break
                last_letter = word[-1] #update last letter
            return word
        
        def generate(self):
            return self.true_title_case(self.generate_base())
            
        def true_title_case(self, text):
            word_exceptions = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', "of"]
            text_parts = re.split(r'(\s|[-–—])', text) 
            
            title_cased_parts = []
            for part in text_parts:
                if part.lower() in word_exceptions and part != text_parts[0] and part != text_parts[-1]:
                    title_cased_parts.append(part.lower())
                elif part.isupper():
                     title_cased_parts.append(part)
                elif part.isalpha():
                    title_cased_parts.append(part.capitalize())
                else:
                    title_cased_parts.append(part)
            
            return "".join(title_cased_parts)
    
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
    print(f"3: create country list dictionary")
    print(f"4: generate random country name")
    num = input("put in a number: ")
    if num not in ["1", "2", "3", "4"]:
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
                next_letter = name[i+1]

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