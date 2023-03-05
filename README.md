# bankerbot
A bot for helping moderators and players track resources in discord social deduction games

dependencies
- python 3.10
- python-dotenv
- discord.py

You will need to create an .env, file placed at the root directory of your project with the values:
DISCORD_TOKEN={your discord token for your bot here}
DISCORD_GUILD={The name of your guild}
BASE_PATH={A path on your machine to which you can write JSON and log files}

## Using the bot:
Only players with guild manage permissions can use the following slash commands:
- /toggle-activity - Enables/disables player-facing commands of the bot
- /add-faction - Adds a faction to the game, with default parameters
- /add-player - Adds a player to the game, with default parameters
- /incarcerate-player - Toggles a player status of incarcerated; True/False
- /kill-player - Toggles a player status of dead; True/False
- /refresh-withdrawals - Refreshes the daily withdraw status for all players

Players that have been added to the game may use the following slash commands:
- /balance - Allows players to view their personal resource balance, or their faction's resource balance
- /transfer - Allows players to transfer resources to another player
- /withdraw - Allows a player to withdraw resources from their faction's holdings
- /deposit - Allows a player to deposit resources into their faction's holdings


