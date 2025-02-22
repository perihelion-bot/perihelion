import asyncio
from dataclasses import dataclass
from enum import IntFlag, Enum
from io import BytesIO
import pickle
import random
import re
import math
from typing import Generator
from PIL import Image
import discord

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

    def __eq__(self, other):
        if self is other: return True
        if isinstance(other, Tile):
            return self.coordinates == other.coordinates
        return super().__eq__(self, other)

    def __hash__(self):
        return self.coordinates[1] << 16 + self.coordinates[0]

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
    military_expenses: int
    money: int
    income: int
    color: tuple[int,int,int]
    war_exhaustion: int
    stability: int

    def __hash__(self):
        return self.id

    async def tick_country(self, instance: "MapGameInstance"):
        self.money += self.income
        self.money -= self.military_expenses
        
        if random.random() < 0.02:
            self.strength = random.randint(3, 10)
            
        if self.money < 0: 
            self.money = 0
            self.strength = 1
            
        if self.warring_countries():
            if self.money <= 0:
                self.war_exhaustion += 8
                self.military_expenses = self.income // 4
            else:
                self.war_exhaustion += 2
                self.military_expenses = max((self.money) // 4, round(self.income * 1.5))
        elif self.war_exhaustion > 0:
            self.war_exhaustion -= 3
            
        for id, relation in self.relations.items():
            if random.random() < 0.005:
                match relation:
                    case self.Relations.WAR: # Treaties are handled elsewhere
                        break
                    case self.Relations.ENEMIES: 
                        if random.random() < 0.4 - max(self.war_exhaustion / 5000, 0.2):
                            instance.event(f"{self.name} has declared war on {instance.countries[id].name}!")
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.WAR)
                        else:
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.NEUTRAL)
                    case self.Relations.NEUTRAL: 
                        if random.random() < 0.5:
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.ENEMIES)
                        else:
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.FRIENDLY)
                    case self.Relations.FRIENDLY: 
                        if rng := random.random() < 0.35:
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.NEUTRAL)
                        elif rng < 0.75:
                            pass # TODO: make proper check for warring countries too
                        else:
                            instance.event(f"{self.name} has allied with {instance.countries[id].name}!")
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.ALLIED)
                    case self.Relations.ALLIED: 
                        if random.random() < 0.2:
                            instance.event(f"{self.name} has stopped being allies with {instance.countries[id].name}!")
                            instance.countries.set_two_way_relation(self, instance.countries[id], self.Relations.FRIENDLY)

            if relation == self.Relations.ALLIED:  
                if warring_countries := (ally := instance.countries[id]).warring_countries():
                    for warring_country in warring_countries:
                        if self.relations[warring_country] == self.Relations.ALLIED:
                            continue
                        country = instance.countries[warring_country]
                        instance.countries.set_two_way_relation(self, country, self.Relations.WAR)
                        instance.event(f"{self.name} has declared war on {country.name} to support their ally of {ally.name}!")
            
            if relation == self.Relations.WAR:  
                if self.war_exhaustion > 200 and random.random() > (self.war_exhaustion - 200) / 20000:
                    instance.event(f"{self.name} has made peace with {instance.countries[id].name}!")
                    instance.countries.declare_peace(instance, self, instance.countries[id])
                
    
    def warring_countries(self):
        return [relation[0] for relation in self.relations.items() if relation[1] == self.Relations.WAR]
    
@dataclass
class MapGameInstance:
    tiles: list[list[Tile]]
    border_tiles: list[Tile]
    _countries: list[Country]
    turn: int
    event_log: str

    @staticmethod
    def parse_image(img):
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
        return MapGameInstance(tiles, [], [], 0, "")

    class CountryAccessor: # Helper class to handle country access in a way that makes sense (e.g. not instance[2])
        def __init__(self, countries_list: list[Country]):
            self._countries_list = countries_list
            self._fake_country_0 = Country("Unclaimed", {}, 0, 0, 0, 0, 0, (100,100,100), 0, 0) 
            
        def __getitem__(self, country_id: int) -> Country | None:
            #if country_id == 0:
            #    return self._fake_country_0 # We do this since 0 should be claimed, but by nobody.
            for country in self._countries_list:
                if country.id == country_id:
                    return country
            raise KeyError(f"Country with id {country_id} not found.")

        def __setitem__(self, country_id: int, country: Country):
            if not isinstance(country, Country):
                raise TypeError("Value must be a Country object.")
            found = False
            for i, existing_country in enumerate(self._countries_list):
                if existing_country.id == country_id:
                    self._countries_list[i] = country # Replace existing country
                    found = True
                    break

            if not found: # Adding a new country
                self._countries_list.append(country)
                # Initialize relations for the new country and all existing countries (two-way)
                for c in self._countries_list:
                    if c.id != country.id:
                        self.set_two_way_relation(c, country, Country.Relations.NEUTRAL)

        def __delitem__(self, country_id: int):
            deleted_country_id = -1
            for i, country in enumerate(self._countries_list):
                if country.id == country_id:
                    deleted_country_id = country.id
                    del self._countries_list[i]
                    break
            else:
                raise KeyError(f"Country with id {country_id} not found.")

            if deleted_country_id != -1:
                # Remove relations involving the deleted country from all remaining countries
                for country in self._countries_list:
                    if deleted_country_id in country.relations:
                        del country.relations[deleted_country_id]


        def append(self, country: Country) -> int:
            if not isinstance(country, Country):
                raise TypeError("Value must be a Country object.")

            existing_ids = {c.id for c in self._countries_list}
            new_id = 1
            while new_id in existing_ids:
                new_id += 1
            country.id = new_id

            self._countries_list.append(country)

            # Initialize relations for the new country and all existing countries (two-way)
            for c in self._countries_list:
                if c.id != country.id:
                    self.set_two_way_relation(c, country, Country.Relations.NEUTRAL)
            return new_id

        def set_two_way_relation(self, country_a: Country, country_b: Country, relation: Country.Relations):
            """Sets a two-way relation between two countries."""
            country_a.relations[country_b.id] = relation
            country_b.relations[country_a.id] = relation

        def get_allies(self, country: Country, found_countries: set[Country] | None = None):
            if found_countries is None:
                found_countries = {country}
            else:
                found_countries |= {country}
            for id, relation in country.relations.items():
                if relation != Country.Relations.ALLIED:
                    continue
                if self[id] in found_countries:
                    continue
                found_countries |= self.get_allies(self[id], found_countries)
            return found_countries
        
        def declare_peace(self, instance: "MapGameInstance", country_a: Country, country_b: Country):
            country_set_a = self.get_allies(country_a)
            country_set_b = self.get_allies(country_b)
            for country_a in country_set_a:
                for country_b in country_set_b:
                    if country_a.relations[country_b.id] != Country.Relations.WAR:
                        continue
                    self.set_two_way_relation(country_a, country_b, Country.Relations.ENEMIES)
        
        def to_dict(self) -> dict[int, Country]:
            """Returns all countries as a dictionary keyed by their IDs."""
            return {country.id: country for country in self._countries_list} 
        
        def all_countries(self):
            for country in self._countries_list:
                yield country           

    @property
    def countries(self):
        return MapGameInstance.CountryAccessor(self._countries)

    class CountryNamer:
        def __init__(self):
            self.weights = {'START': {'a': 76, 'b': 95, 'c': 96, 'd': 36, 'e': 29, 'f': 28, 'g': 56, 'h': 37, 'i': 38, 'j': 24, 'k': 61, 'l': 48, 'm': 93, 'n': 40, 'o': 10, 'p': 71, 'q': 3, 'r': 39, 's': 99, 't': 69, 'u': 27, 'v': 22, 'y': 11, 'z': 11, 'w': 22, "'": 2, 'x': 1, ' ': 1}, 'a': {'f': 17, 'n': 403, 'l': 152, 'END': 328, ' ': 38, 'r': 153, 'u': 48, 'z': 18, 'i': 60, 'h': 19, 'm': 47, 's': 56, 'd': 42, 'b': 36, 't': 123, '-': 7, 'q': 4, 'e': 2, 'p': 15, 'k': 38, 'o': 5, 'g': 22, 'w': 11, 'y': 18, 'c': 18, 'j': 10, 'a': 10, 'v': 24, "'": 2, 'x': 9}, 'f': {'g': 2, 'a': 12, 'r': 15, 'i': 9, ' ': 1, 'END': 3, 'u': 7, 's': 2, 'f': 2, '-': 1, 'e': 24, 'o': 6, 'l': 4}, 'g': {'h': 16, 'e': 39, 'o': 31, 'u': 26, 'l': 6, 'i': 11, 'a': 60, 'y': 4, 'r': 31, 'END': 29, 'd': 1, 'g': 3, 'w': 3, 'b': 1, 'c': 1, 't': 1, 'n': 3, 'z': 1, 'x': 2, ' ': 4, 'k': 2, 'm': 1, '-': 8}, 'h': {'a': 76, 'r': 6, 'END': 21, 'u': 27, 'e': 36, 'i': 47, 'o': 33, 's': 2, 't': 4, ' ': 20, 'l': 3, 'd': 2, 'y': 4, 'w': 6, 'n': 2, 'b': 1, '-': 1, 'c': 1, 'k': 2}, 'n': {'i': 120, 'END': 146, 'd': 98, 'g': 81, 't': 46, 'a': 106, 'e': 78, ' ': 83, 'm': 3, 'l': 6, 'c': 24, 'y': 12, 'o': 39, 's': 18, 'k': 11, 'z': 8, 'u': 5, 'n': 8, 'j': 4, 'r': 1, 'f': 11, '-': 5, 'p': 1, 'h': 2, 'b': 8, 'w': 2}, 'i': {'s': 78, 'a': 250, 'g': 11, 'n': 135, 'j': 6, 'u': 4, 'z': 4, 'v': 21, 'l': 32, 'END': 62, 'c': 62, 'r': 33, 'b': 14, 't': 55, 'o': 27, 'e': 55, 'q': 3, 'p': 21, ' ': 20, 'w': 1, 'k': 13, 'm': 25, 'd': 20, 'f': 3, 'y': 8, '-': 3, 'h': 2, 'x': 2, "'": 1, 'i': 1}, 's': {'t': 95, 'END': 69, 'h': 41, 'n': 4, 'w': 10, 'o': 82, 'a': 56, 's': 32, 'i': 60, 'r': 4, 'c': 13, 'l': 19, ' ': 27, 'e': 28, 'u': 16, 'p': 10, 'y': 9, 'k': 11, '-': 1, 'm': 1, 'z': 1, 'v': 2}, 't': {'a': 94, 'i': 69, 'r': 46, 's': 13, 'e': 82, 'END': 61, 'o': 55, 'h': 34, 'v': 3, 'u': 32, ' ': 58, 't': 12, 'z': 2, 'y': 10, 'n': 5, 'l': 5, 'w': 1, 'm': 1, 'k': 1, '-': 1, 'c': 1}, 'l': {'b': 8, 'g': 13, 'a': 101, 'i': 110, 'END': 26, ' ': 20, 'e': 61, 'o': 43, 'v': 7, 'y': 8, 'u': 23, 'd': 11, 't': 9, 'l': 22, 'k': 3, 'w': 1, '-': 2, 'h': 3, 'm': 4, 's': 3, 'f': 1, 'z': 1, 'p': 2}, 'b': {'a': 78, 'u': 42, 'e': 31, 'h': 1, 'o': 32, 'r': 14, 'l': 6, 'i': 25, 'y': 4, ' ': 3, 'w': 3, 'END': 5, 'b': 1, 'd': 1, 'k': 1}, 'e': {'r': 127, 'n': 110, 's': 61, 'l': 44, 'END': 109, 'g': 21, 'i': 15, 'p': 10, ' ': 34, 'c': 25, 'q': 2, 'a': 41, 't': 63, 'o': 26, 'e': 9, 'm': 25, 'b': 6, 'x': 8, 'w': 8, 'd': 35, 'v': 10, 'y': 5, 'k': 5, 'z': 6, 'j': 6, 'u': 7, "'": 17, 'f': 1, '-': 15, 'h': 1}, 'r': {'i': 108, 'r': 9, 'a': 175, 'b': 10, 'g': 30, 'm': 27, 'u': 44, 'z': 8, 'k': 9, 'd': 18, 'o': 56, 'e': 70, 'END': 42, 'y': 17, 's': 13, 'l': 7, 't': 18, 'w': 6, '-': 3, 'f': 1, 'n': 14, ' ': 14, 'h': 6, 'c': 7, 'q': 1, 'p': 2, 'v': 1}, 'd': {'o': 29, ' ': 24, 'a': 54, 'e': 77, 'i': 34, 'END': 54, "'": 1, 'j': 1, 'u': 8, 's': 10, 'r': 2, 'z': 2, 'h': 3, 'd': 2, 'y': 4, 'b': 1, 't': 1, 'm': 1, 'n': 2, 'l': 1}, 'o': {'r': 81, 'l': 56, 's': 34, 'v': 60, 't': 21, 'END': 54, ' ': 8, 'd': 18, 'o': 3, 'n': 123, 'm': 62, 'i': 10, 'a': 10, 'u': 36, 'p': 25, 'c': 39, 'z': 5, 'g': 14, 'b': 8, 'f': 1, 'k': 5, 'y': 6, 'w': 11, 'q': 2, 'h': 4, '-': 5, 'j': 1}, 'u': {'a': 35, 'd': 8, 's': 55, 'm': 10, 't': 36, 'n': 56, 'l': 20, 'r': 68, 'b': 11, 'i': 17, 'END': 33, 'y': 1, 'w': 4, 'x': 1, 'e': 7, 'g': 11, 'c': 11, 'v': 5, 'k': 21, 'z': 2, '-': 5, 'p': 13, ' ': 2, 'j': 2, 'o': 2, 'h': 2, "'": 1}, ' ': {'a': 53, 'b': 12, 'h': 13, 'f': 16, 'v': 6, 'r': 16, 'd': 13, 's': 83, 'g': 16, 'i': 14, 'z': 2, 'k': 27, 'm': 19, 'n': 11, 'l': 14, 't': 16, 'p': 28, 'e': 8, 'o': 4, 'c': 27, 'y': 6, 'j': 3, 'q': 2, 'u': 4, 'w': 1, ' ': 1}, 'm': {'e': 48, 'a': 125, 'END': 17, 'b': 23, 'o': 57, 'i': 23, 'y': 6, 'l': 1, 'c': 1, 'm': 12, 'u': 10, 't': 4, ' ': 4, 'p': 4, 'r': 1, 'k': 1}, 'z': {'e': 17, 'i': 14, 'a': 21, 's': 1, 'b': 5, 'u': 6, 'END': 4, 'v': 1, 'm': 1, 'h': 3, 'o': 4, 'c': 1, ' ': 1, 't': 1}, 'j': {'a': 22, 'i': 11, 'o': 7, 'u': 10, 'e': 3, 'd': 3, 'END': 1}, 'v': {'i': 73, 'e': 26, 'o': 22, 'a': 36, 's': 1, 'END': 3, 'g': 1, 'l': 1, 'y': 1}, 'w': {'a': 42, 'i': 7, ' ': 6, 'e': 21, 'o': 3, 'h': 1, 'END': 6, 'u': 1, 'y': 2, 'r': 1, 'n': 3, 'f': 1}, 'k': {'i': 17, 'END': 18, 'a': 54, 'h': 40, 'e': 13, 'o': 27, 'u': 18, 'y': 4, 'm': 2, 'r': 14, 'n': 1, 'w': 2, ' ': 11, 'k': 2, '-': 1, 'f': 2, 'l': 2}, 'c': {'a': 66, 'e': 29, 'END': 13, 'h': 55, 'o': 60, 'r': 21, 'u': 5, 'y': 5, 'z': 7, 'c': 5, 'i': 47, ' ': 8, 't': 4, 'k': 8, 'l': 2, 'n': 1}, 'p': {'u': 11, 'r': 23, 't': 4, 'i': 16, 'a': 41, 'e': 42, 'h': 7, 'p': 11, 'o': 32, 'l': 20, 'g': 1, ' ': 7, 'END': 2, 's': 2}, "'": {'i': 2, 'a': 1, 's': 17, 'd': 1, 'k': 2, 'u': 1}, 'y': {'p': 4, 'END': 34, 'a': 33, 'r': 8, 'z': 2, 's': 3, 'c': 2, 'e': 7, ' ': 19, 't': 2, 'u': 10, 'o': 4, 'i': 2, 'd': 2, 'l': 6, 'f': 1, '-': 1, 'n': 3, 'k': 2}, 'q': {'u': 8, 'END': 3, 'a': 2, 'i': 2, ' ': 1, 'o': 1}, '-': {'b': 7, 'l': 5, 'e': 2, 'r': 3, 'f': 3, 'm': 3, 'p': 2, 'k': 3, 'u': 3, 't': 2, 'n': 2, 'c': 2, 'g': 2, 'h': 4, 's': 8, 'a': 3, 'w': 2, 'v': 2, 'o': 1}, 'x': {'e': 8, 'i': 10, 'END': 2, 'o': 1, 'a': 2}}
            self.min_length = 4
            self.max_length = 24
            self.ending_mult = [0, 0, 0, 0, 0.2, 0.3, 0.5, 0.7, 1, 1.2, 1.6, 2, 2.5, 3, 3.5, 4, 5, 7, 20, 999, 999, 999, 999, 999]
            self.space_mult = [0, 0, 0.1, 0.2, 0.5, 0.55, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
            self.descriptor_chance = 0.15

        def generate_base(self):
            word = "" # start with the initial word
            last_letter = "START"
            time_since_space = 0 # pretend it starts with a space
            while True:
                picks = list(self.weights[last_letter].keys()) # possible next letters
                pick_weights = list(self.weights[last_letter].values()) # chance for each next letter
                try:
                    pick_weights[picks.index("END")] *= self.ending_mult[len(word)] * (time_since_space > 1)
                except ValueError: # we can fail if it's not in the list
                    pass
                try:
                    pick_weights[picks.index(" ")] *= self.space_mult[time_since_space]
                except ValueError:
                    pass
                if len(picks) == 0: # we have reached a letter that never gets followed (shouldn't be necessary in most cases but whatever)
                    break
                genned = random.choices(picks, weights=pick_weights)[0] # add letter
                if genned == " ":
                    time_since_space = 0
                else:
                    time_since_space += 1
                if genned != "END":
                    word += genned
                else:
                    if len(word) >= self.min_length:
                        break
                if len(word) >= self.max_length:
                    break
                last_letter = word[-1] # update last letter
            if word[-2] == " ": # they snuck a 1 letter word past us
              word = word[:-2] # exterminate it
            return word

        def generate(self):
            descriptors = ["north", "south", "east", "west", "free", "new"]
            formats = ["$ republic", "$ republic", "$ kingdom", "$ kingdom", "$ federation", "$", "$", "$ confederation", "$ horde", "$ union", "$ empire", "$ empire", "united kingdom of $", "united kingdoms of $", "united states of $"]
            name = self.generate_base()
            if random.random() < self.descriptor_chance:
              name = random.choice(descriptors) + " " + name
            name = random.choice(formats).replace("$", name)
            return self.true_title_case(name)

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

    def all_tiles(self) -> list[Tile] | None:
        return [tile for row in self.tiles for tile in row]

    def save_to_file(self):
        with open("data/mapgame.pickle", "wb") as f:
            pickle.dump(self, f)

    async def render(self):

        def clr_blend(color1, color2, amount: float = 0.5):
            r1, g1, b1 = color1
            r2, g2, b2 = color2

            r = r1 + (r2 - r1) * amount
            g = g1 + (g2 - g1) * amount
            b = b1 + (b2 - b1) * amount

            return (int(r), int(g), int(b))

        countries = self.countries.to_dict()

        img = Image.new(mode="RGB", size=(len(self.tiles), len(self.tiles[0])), color=(35,49,77))
        pixels = img.load()
        for row in self.tiles:
            for tile in row:
                if tile.flags == Tile.TileFlags.WATER:
                    pass
                if tile.flags == Tile.TileFlags.CROSSABLE: # Water crossing
                    pixels[tile.coordinates[0], tile.coordinates[1]] = clr_blend((35,49,77), countries.get(tile.owner_id, Country("", {}, 0,0,0,0,0,(100,100,100),0,0)).color)
                if tile.flags == Tile.TileFlags.LAND: # Uncrossable land
                    pixels[tile.coordinates[0], tile.coordinates[1]] = (25,25,25)
                if tile.flags == Tile.TileFlags.LAND | Tile.TileFlags.CROSSABLE:
                    pixels[tile.coordinates[0], tile.coordinates[1]] = countries.get(tile.owner_id, Country("", {}, 0,0,0,0,0,(100,100,100),0,0)).color
                # DEBUG
                # if tile in self.border_tiles:
                #    pixels[tile.coordinates[0], tile.coordinates[1]] = (200,0,0)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return discord.File(buffer, 'mapgame.png')

    def event(self, event: str):
        self.event_log += event
        self.event_log += "\n"
        
    def get_events(self) -> str:
        """Note that this function clears the event log.
        """
        log = self.event_log
        self.event_log = ""
        return log
            
    async def mapgame_step(self):
        self.event_log = ""
        for i in range(5):
            await asyncio.sleep(0)
            await self.mapgame_step_expand()
        for country in self.countries.all_countries():
            await country.tick_country(self)
        self.turn += 1
        self.save_to_file()

    async def mapgame_step_expand(self):
        roughness = 0.5 #0 is fully smooth, 1 is fully rough. somewhere in the middle is best

        additional_income = {}
        new_border_tiles = set()
        random.seed(random.random() + self.turn)
        expansion_seed = random.random()
        for tile in self.border_tiles:
            owner = self.countries[tile.owner_id]
            owners_takeable = owner.warring_countries()
            owners_takeable.append(owner.id)
            coords = tile.coordinates
            neighbors: tuple[Tile] = () # Initialize as empty tuple, then populate correctly
            if coords[0] + 1 < len(self.tiles):
                neighbors += (self.tiles[coords[0]+1][coords[1]],)
            if coords[0] - 1 >= 0:
                neighbors += (self.tiles[coords[0]-1][coords[1]],)
            if coords[1] + 1 < len(self.tiles[0]):
                neighbors += (self.tiles[coords[0]][coords[1]+1],)
            if coords[1] - 1 >= 0:
                neighbors += (self.tiles[coords[0]][coords[1]-1],)

            neighbors_crossable = [neighbor for neighbor in neighbors if Tile.TileFlags.CROSSABLE in neighbor.flags]
            candidates = [neighbor for neighbor in neighbors_crossable if neighbor.owner_id == 0]
            for candidate in candidates: # expansion
                if (random.random() * 100) < owner.strength * math.log(owner.military_expenses+2, 2): # Take the tile!
                    candidate.owner_id = tile.owner_id
                    additional_income[tile.owner_id] = additional_income.get(tile.owner_id, 0) + 1
                    new_border_tiles.add(candidate)
            risk = [neighbor for neighbor in neighbors_crossable if neighbor.owner_id in owners_takeable] 
            winning_countries = {}
            country_tiles = {}
            if risk and not all([neighbor.owner_id == tile.owner_id for neighbor in risk]): # are we in a warzone
                for candidate in risk: # war
                    if candidate.owner_id not in winning_countries:
                        winning_countries[candidate.owner_id] = 0
                        country_tiles[candidate.owner_id] = 0
                    random.seed(expansion_seed * candidate.coordinates[0] + candidate.coordinates[1]) # designed to stay the same for the same tile on the same turn and in no other case
                    strength = random.random()
                    winning_countries[candidate.owner_id] += strength
                    country_tiles[candidate.owner_id] += 1
                winning_countries = {k: v/country_tiles[k]**roughness for k, v in winning_countries.items()}
                winner = max(winning_countries, key=winning_countries.get)
                if tile.owner_id != winner:
                    additional_income[winner] = additional_income.get(winner, 0) + 1
                    additional_income[tile.owner_id] = additional_income.get(tile.owner_id, 0) - 1
                    tile.owner_id = winner
                new_border_tiles.add(tile)
            if len([neighbor for neighbor in neighbors_crossable if neighbor.owner_id != tile.owner_id]) != 0:
                new_border_tiles.add(tile)
        self.border_tiles = list(new_border_tiles)
        if additional_income.get(0, False):
            del additional_income[0]
        for country_id in additional_income:
            self.countries[country_id].income += additional_income[country_id]