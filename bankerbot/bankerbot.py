# bankerbot.py
import os
import discord
from dotenv import load_dotenv
from discord import app_commands
from typing import List, Optional, Literal
import banker_dom
from banker_dom import Game, Player, Faction
from logging_manager import logger

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BASE_PATH = os.getenv('BASE_PATH')

game_factions = Literal["Van der Linde Gang",
                        "O'Driscoll Boys",
                        "Lemoyne Raiders",
                        "Del Lobo Gang",
                        "Wapiti Indians",
                        "Pinkerton Detective Agency",
                        "Robber Baron - Cornwall",
                        "Robber Baron - Bronte",
                        "Robber Baron - Braithwaite",
                        "Robber Baron - Gray"]


class BankerBotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=947928220093788180))
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = BankerBotClient()
tree = app_commands.CommandTree(client)


@tree.command(name="toggle-activity",
              description="Enables/Disables bot commands for players",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def toggle_activity(interaction: discord.Interaction,
                          active: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    game.is_active = True if active == 'True' else False

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Game state has been set to {active}!', ephemeral=True)


@tree.command(name="add-faction",
              description="Adds a faction to the game",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def add_faction(interaction: discord.Interaction,
                      faction: game_factions,
                      assets: app_commands.Range[int, 0, 50] = 0):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    existing_faction = game.get_faction(faction)

    if existing_faction is None:
        new_faction = Faction(player_ids=[],
                              faction_name=faction,
                              assets=assets)
        game.add_faction(new_faction)

        await write_game(game, BASE_PATH)
        await interaction.response.send_message(f'Added faction {faction} to game with initial assets {assets}',
                                                ephemeral=True)
    else:
        await interaction.response.send_message(f'Failed to add faction {faction} to game!', ephemeral=True)


@tree.command(name="add-player",
              description="Adds a player to the game",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def add_player(interaction: discord.Interaction,
                     player: discord.Member,
                     faction: game_factions,
                     assets: app_commands.Range[int, 0, 50] = 0,
                     faction_boss: Optional[Literal['True', 'False']] = 'False',
                     withdraw_limit: Optional[int] = 2):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    game_faction = game.get_faction(faction)
    existing_faction = game.get_faction_of_player(player.id)

    # Faction needs to exist first
    if game_faction is None:
        await interaction.response.send_message(
            f'Faction {faction} has not been defined yet! Please define this faction first!', ephemeral=True)
        return

    # Player can only exist in one faction at a time
    if existing_faction is not None:
        await interaction.response.send_message(
            f'Player already found in faction {existing_faction.faction_name}! Player can only exist in one faction!',
            ephemeral=True)
        return

    if game.get_player(player.id) is None:
        new_player = Player(player_id=player.id,
                            player_discord_name=player.name,
                            faction_name=faction,
                            assets=assets,
                            withdraw_limit=withdraw_limit,
                            is_faction_boss=True if faction_boss == 'True' else False)
        game.add_player(new_player)
        game_faction.add_player(player.id)
        await write_game(game, BASE_PATH)
        await interaction.response.send_message(f'Added player {player.name} to game!', ephemeral=True)
    else:
        await interaction.response.send_message(f'Failed to add {player.name} to game!', ephemeral=True)

@tree.command(name="incarcerate-player",
              description="Toggles a player status of being incarcerated or not.",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def incarcerate_player(interaction: discord.Interaction,
                     player: discord.Member,
                     incarcerated: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    this_player = game.get_player(player.id)
    if this_player is None:
        await interaction.response.send_message(f'Player {player.name} is not currently defined in this game!',
                                                ephemeral=True)
    else:
        this_player.is_incarcerated = True if incarcerated == 'True' else False

        await write_game(game, BASE_PATH)
        await interaction.response.send_message(f'Set incarceration status of {player.name} to {incarcerated}!',
                                                ephemeral=True)


@tree.command(name="kill-player",
              description="Toggles a player status of being dead or not.",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def kill_player(interaction: discord.Interaction,
                     player: discord.Member,
                     dead: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    this_player = game.get_player(player.id)
    if this_player is None:
        await interaction.response.send_message(f'Player {player.name} is not currently defined in this game!',
                                                ephemeral=True)
    else:
        this_player.is_dead = True if dead == 'True' else False

        await write_game(game, BASE_PATH)
        await interaction.response.send_message(f'Set alive status of {player.name} to {dead}!', ephemeral=True)


@tree.command(name="refresh-withdrawals",
              description="Toggles a player status of being dead or not.",
              guild=discord.Object(id=947928220093788180))
@app_commands.default_permissions(manage_guild=True)
async def refresh_withdrawals(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    for player in game.players:
        if not player.is_incarcerated and not player.is_dead:
            player.daily_withdraw_available = True

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Refreshed the daily withdrawal allowance for all players!',
                                            ephemeral=True)


@tree.command(name="deposit",
              description="Deposit assets from your personal stash to your faction's holdings",
              guild=discord.Object(id=947928220093788180))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def deposit(interaction: discord.Interaction,
                  amount: app_commands.Range[int, 0, 20]):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(
            f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    depositing_player = game.get_player(interaction.user.id)
    player_faction = game.get_faction_of_player(interaction.user.id)

    if depositing_player is None:
        await interaction.response.send_message(f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
    elif player_faction is None:
        await interaction.response.send_message(f'Player {interaction.user.name} does not have a valid faction!', ephemeral=True)
    elif depositing_player.is_dead or depositing_player.is_incarcerated:
        await interaction.response.send_message(f'Incarcerated or dead players cannot deposit assets!')
    else:
        if depositing_player.assets < amount:
            await interaction.response.send_message(
                f'Amount {amount} exceeds available assets of {depositing_player.assets}! Cannot deposit that amount!',
                ephemeral=True)
            return
        else:
            depositing_player.set_assets(depositing_player.assets - amount)
            player_faction.set_assets(player_faction.assets + amount)

            await write_game(game, BASE_PATH)
            await interaction.response.send_message(f'Deposited {amount} assets to {player_faction.faction_name}',
                                                    ephemeral=True)
            await interaction.followup.send(f'Current personal assets are {depositing_player.assets}', ephemeral=True)


@tree.command(name="withdraw",
              description="Withdraw assets from your faction's holdings into your personal stash",
              guild=discord.Object(id=947928220093788180))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def withdraw(interaction: discord.Interaction,
                   amount: app_commands.Range[int, 0, 20]):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(
            f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    withdrawing_player = game.get_player(interaction.user.id)
    player_faction = game.get_faction_of_player(interaction.user.id)

    if withdrawing_player is None:
        await interaction.response.send_message(f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
    elif player_faction is None:
        await interaction.response.send_message(f'Player {interaction.user.name} does not have a valid faction!',ephemeral=True)
    elif withdrawing_player.is_dead or withdrawing_player.is_incarcerated:
        await interaction.response.send_message(f'Incarcerated or dead players cannot deposit assets!')
    else:
        if player_faction.assets < amount:
            await interaction.response.send_message(
                f'Amount {amount} exceeds available assets of {player_faction.assets}! Cannot withdraw that amount!',
                ephemeral=True)
        elif not withdrawing_player.daily_withdraw_available:
            await interaction.response.send_message(f'No remaining withdrawals available for this phase!',
                                                    ephemeral=True)
        else:
            withdrawing_player.daily_withdraw_available = False
            player_faction.set_assets(player_faction.assets - amount)
            withdrawing_player.set_assets(withdrawing_player.assets + amount)

            await write_game(game, BASE_PATH)
            await interaction.response.send_message(
                f'Withdrew {amount} assets from {player_faction.faction_name} holdings!', ephemeral=True)
            await interaction.followup.send(f'Current personal assets are {withdrawing_player.assets}', ephemeral=True)


@tree.command(name="transfer",
              description="Transfer assets from your personal stash to another player",
              guild=discord.Object(id=947928220093788180))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def transfer(interaction: discord.Interaction,
                   player: discord.Member,
                   amount: app_commands.Range[int, 0, 20]):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(
            f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    sending_player = game.get_player(interaction.user.id)
    receiving_player = game.get_player(player.id)

    if sending_player is None:
        await interaction.response.send_message(
            f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
        return
    elif receiving_player is None:
        await interaction.response.send_message(f'Player {player.name} is not currently defined in this game!',
                                                ephemeral=True)
        return
    elif sending_player.is_dead or sending_player.is_incarcerated:
        await interaction.response.send_message(f'Incarcerated or dead players cannot send or receive assets!')
        return
    elif receiving_player.is_dead or receiving_player.is_incarcerated:
        await interaction.response.send_message(f'Incarcerated or dead players cannot send or receive assets!')
        return
    else:
        if sending_player.assets < amount:
            await interaction.response.send_message(
                f'Amount {amount} exceeds available assets of {sending_player.assets}! Cannot send that amount!',
                ephemeral=True)
            return
        else:
            sending_player.set_assets(sending_player.assets - amount)
            receiving_player.set_assets(receiving_player.assets + amount)

            await write_game(game, BASE_PATH)
            await interaction.response.send_message(f'Transferred {amount} assets to {player.name}', ephemeral=True)
            await interaction.followup.send(f'Current personal assets are {sending_player.assets}', ephemeral=True)


@tree.command(name="balance",
              description="Get the current balance of assets in your personal stash, or your faction's holdings",
              guild=discord.Object(id=947928220093788180))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def balance(interaction: discord.Interaction,
                  of_type: Literal['Player', 'Faction']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(
            f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    requesting_player = game.get_player(interaction.user.id)

    if of_type == "Player":
        if requesting_player is None:
            await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
        else:
            await interaction.response.send_message(
                f'Current personal assets for player {interaction.user.name} is {requesting_player.assets}',
                ephemeral=True)
    else:
        if requesting_player is None:
            await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
            return
        elif not requesting_player.is_faction_boss:
            await interaction.response.send_message(f'Only faction-boss players may view faction asset holdings!', ephemeral=True)
            return

        requested_faction = game.get_faction_of_player(interaction.user.id)
        if requested_faction is None:
            await interaction.response.send_message(f'Could not find faction for player {interaction.user.name}!', ephemeral=True)
        else:
            await interaction.response.send_message(
                f'Current faction holdings for Faction {requested_faction.faction_name} is {requested_faction.assets}',
                ephemeral=True)

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Cooldown is in force, please wait for {round(error.retry_after)} seconds", ephemeral=True)
    else:
        raise error


async def get_game(path: str) -> Game:
    json_file_path = f'{path}/game.json'
    logger.info(f'Grabbing game info from {json_file_path}')
    return banker_dom.read_json_to_dom(json_file_path)


async def write_game(game: Game, path: str):
    json_file_path = f'{path}/game.json'
    logger.info(f'Wrote game data to {json_file_path}')
    banker_dom.write_dom_to_json(game, json_file_path)


def log_interaction_call(interaction: discord.Interaction):
    logger.info(
        f'Received command {interaction.command.name} with parameters {interaction.data} initiated by user {interaction.user.name}')


client.run(TOKEN)
