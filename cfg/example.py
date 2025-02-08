import datetime

TOKEN = "Token here"

BOT_NAME = "Apohelion" # This shows up in /info.

VERSION = f"9.9.9.99+buildtime_{int(datetime.datetime.now().timestamp())}" # This shows up in /info.

PRESENCE = "farther than pluto" # This shows up in the "Playing ..." area

LOGGING = {"LEVEL": "DEBUG"} # This should be one of DEBUG, INFO, WARNING, ERROR, CRITICAL

SYNCING = {"SHOULD_SYNC": False, "SERVER": 1234567890} # Decides if we should sync commands. Set server to 0 for global sync.

EMBED = {"COLOR": 0xff8a8c, "FOOTER": f"Perihelion testing | v{VERSION}"} # This is for the embed templates.

ERROR_LOGGING_CHANNEL = 1234567890123456789 # Errors will get logged to this channel.

MAPGAME = {
    "ENABLED": True, # Whether the mapgame system should be enabled.
    "STEPRATE": 10, # How often ticks happen, in seconds. e.g. 10s/step
    "CHANNEL": 1234567890123456789 # Mapgame steps will be sent here.
} 

DONT_LOAD_COGS = ["cogs.100-commands.test"] # This only works for cogs (so those in the cogs folder)

DEVELOPERS = [230873196247777280] # Should be a list of user IDs
