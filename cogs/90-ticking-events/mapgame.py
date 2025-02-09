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
        
    relations = dict[int, Relations]
    id: int
    strength: int
    balance: int
    income: int

@dataclass
class MapGameInstance:
    tiles: list[list[Tile]]
    border_tiles: list[Tile]
    countries: list[Country]
    
    @staticmethod
    def parse_image(img: Image):
        width, height = img.size

        for x in range(width):
            for y in [48]:#range(height):
                _r, g, b, _a = img.getpixel((x, y))
                match b:
                    case 255:
                        flags = Tile.TileFlags.WATER
                    case 128:
                        flags = Tile.TileFlags.CROSSABLE
                    case 0:
                        flags = Tile.TileFlags.LAND | Tile.TileFlags.CROSSABLE
                income = g >> 4
                print(f"{x}, {y} | flags: {flags!r}, income: {income}")

class MapGameCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: mapgame loaded")
    
    def mapgame_step(self):
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
        data = MapGameInstance.parse_image(image)
    if num == "2":
        ...