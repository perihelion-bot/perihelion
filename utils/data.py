import os
import json
from typing import Any, Dict, List, Literal, Optional, Union
from peridata import Property, PersistentStorage

USER_AVAILABLE_DATA: Dict[str, Property[Any]] = {
    "Global: Compact mode": Property[bool](False, False),
    "Rolling: Default roll": Property[str]("1d100", False),
    "Define: English-only": Property[bool](False, False),
    "RngSim: Highscore": Property[float](float(0), True),
}

GUILD_AVAILABLE_DATA: Dict[str, Property[Any]] = {
}

GLOBAL_DATA: Dict[str, Property[Any]] = {
}

class IdentifierDataManager(PersistentStorage):
    def __init__(self, entity_type: str, entity_id: Union[int, str], available_data: Dict[str, Property]):
        file_path = f'data/{entity_type}s/{entity_id}.json'
        super().__init__(available_data, file_path)

class UserDataManager(IdentifierDataManager):
    def __init__(self, user_id: int):
        super().__init__("user", user_id, USER_AVAILABLE_DATA)

class GuildDataManager(IdentifierDataManager):
    def __init__(self, guild_id: int):
        super().__init__("guild", guild_id, GUILD_AVAILABLE_DATA)

class GlobalDataManager(PersistentStorage):
    def __init__(self):
        super().__init__(GLOBAL_DATA, "data/global.json")

def get_data_manager(entity_type: Literal["user", "guild", "global"], entity_id: int) -> PersistentStorage:
    """Returns a PersistentStorage instance based on entity type and entity id."""
    if entity_type == "user":
        return UserDataManager(entity_id)
    elif entity_type == "guild":
        return GuildDataManager(entity_id)
    elif entity_type == "global":
        return GlobalDataManager()
    else:
        raise ValueError(f"Invalid entity type: {entity_type}")
