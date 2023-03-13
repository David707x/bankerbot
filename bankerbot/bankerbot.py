# bankerbot.py
import os
import discord
from dotenv import load_dotenv
from discord import app_commands, Member, Guild
from typing import List, Optional, Literal
import banker_dom
from banker_dom import Game, Player, Faction, Round, Vote
import embed_builder
from logging_manager import logger
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
PLAYER_ROLE_ID = int(os.getenv('PLAYER_ROLE_ID'))
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

embed_choices = embed_builder.build_embeds()

class BankerBotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = BankerBotClient()
tree = app_commands.CommandTree(client)

async def player_list_autocomplete(interaction: discord.Interaction,
                                   current: str,
                             ) -> List[app_commands.Choice[str]]:
    game = await get_game(BASE_PATH)
    players = await get_valid_players(game.players)
    return [
        app_commands.Choice(name=player.player_discord_name, value=str(player.player_id))
        for player in players
    ]

async def get_valid_players(players: List[Player]) -> List[Player]:
    player_list = []
    for player in sorted(players, key=lambda e: e.player_discord_name.lower()):
        if not player.is_dead:
            player_list.append(player)
    return player_list

@tree.command(name="toggle-activity",
              description="Enables/Disables bot commands for players",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def toggle_activity(interaction: discord.Interaction,
                          active: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    game.is_active = True if active == 'True' else False

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Game state has been set to {active}!', ephemeral=True)


@tree.command(name="post-embed",
              description="Posts a pre-computed embed to a channel",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(embed=embed_choices)
async def post_embed(interaction: discord.Interaction,
                     embed: str,
                     channel: discord.TextChannel):
    log_interaction_call(interaction)
    embed_list = embed_builder.get_embed_dict().get(embed)

    await interaction.response.send_message(f"Current region control standings:")

    for embed_to_post in embed_list:
        await channel.send(embed=embed_to_post)


@tree.command(name="add-faction",
              description="Adds a faction to the game",
              guild=discord.Object(id=GUILD_ID))
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
              guild=discord.Object(id=GUILD_ID))
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
                            tension=0,
                            withdraw_limit=withdraw_limit,
                            is_faction_boss=True if faction_boss == 'True' else False)
        game.add_player(new_player)
        game_faction.add_player(player.id)
        await write_game(game, BASE_PATH)
        await interaction.response.send_message(f'Added player {player.name} to game!', ephemeral=True)
    else:
        await interaction.response.send_message(f'Failed to add {player.name} to game!', ephemeral=True)

@tree.command(name="start-round",
              description="Creates and enables the current round, if possible",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def start_round(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    latest_round = game.get_latest_round()

    if latest_round is None:
        new_round = Round(votes=[], round_number=1, is_active_round=True)
        game.add_round(new_round)
    elif latest_round.is_active_round:
        await interaction.response.send_message(f'There is already an active round; you must end the existing round first before creating another', ephemeral=True)
        return
    else:
        new_round = Round(votes=[], round_number=latest_round.round_number + 1, is_active_round=True)
        game.add_round(new_round)

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Created round {new_round.round_number}!', ephemeral=True)


@tree.command(name="end-round",
              description="Ends the current round, if possible",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def end_round(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is not currently an active round to end!', ephemeral=True)
        return
    else:
        latest_round.is_active_round = False

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Ended round {latest_round.round_number}!', ephemeral=True)

@tree.command(name="incarcerate-player",
              description="Toggles a player status of being incarcerated or not.",
              guild=discord.Object(id=GUILD_ID))
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
        await interaction.response.send_message(f'Set incarceration status of {player.name} to {incarcerated}!', ephemeral=True)

@tree.command(name="kill-player",
              description="Toggles a player status of being dead or not.",
              guild=discord.Object(id=GUILD_ID))
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
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def refresh_withdrawals(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    for player in game.players:
        if not player.is_incarcerated and not player.is_dead:
            player.daily_withdraw_available = True

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Refreshed the daily withdrawal allowance for all players!', ephemeral=True)


@tree.command(name="deposit",
              description="Deposit assets from your personal stash to your faction's holdings",
              guild=discord.Object(id=GUILD_ID))
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
              guild=discord.Object(id=GUILD_ID))
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
              guild=discord.Object(id=GUILD_ID))
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
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def balance(interaction: discord.Interaction,
                  of_type: Literal['Player', 'Faction', 'Tension']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    requesting_player = game.get_player(interaction.user.id)

    if of_type == "Player":
        if requesting_player is None:
            await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
        else:
            await interaction.response.send_message(f'Current personal assets for player {interaction.user.name} is {requesting_player.assets}', ephemeral=True)

    elif of_type == "Tension":
        if requesting_player is None:
            await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
        else:
            await interaction.response.send_message(f'Current tension level for player {interaction.user.name} is {requesting_player.tension}', ephemeral=True)
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
            await interaction.response.send_message(f'Current faction holdings for Faction {requested_faction.faction_name} is {requested_faction.assets}', ephemeral=True)

@tree.command(name="role-player-test",
              description="Select only a specific player from a list",
              guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(player=player_list_autocomplete)
async def role_player_test(interaction: discord.Interaction,
                           player: str):
    log_interaction_call(interaction)

    await interaction.response.send_message(f'Got player {player}!', ephemeral=True)


@tree.command(name="vote-player",
              description="Votes for a particular player",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def vote_player(interaction: discord.Interaction,
                      player: Optional[discord.Member] = None,
                      other: Optional[Literal['No Vote', 'Unvote']] = None):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    latest_round = game.get_latest_round()
    if latest_round is None or not latest_round.is_active_round:
        await interaction.response.send_message(f'No currently active round found for this game!', ephemeral=True)
        return

    requesting_player = game.get_player(interaction.user.id)
    if requesting_player is None:
        await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
        return

    voted_player = None if player is None else game.get_player(player.id)

    if voted_player is not None and voted_player.is_dead:
        await interaction.response.send_message(f'Player {voted_player.player_discord_name} is dead and cannot be voted!', ephemeral=True)
        return

    if voted_player is None and other is None:
        await interaction.response.send_message(f'Player {player.name} was not found in this game!', ephemeral=True)
        return
    else:
        round_current_player_vote = latest_round.get_player_vote(requesting_player.player_id)

        if voted_player is None and other is not None:
            if round_current_player_vote is None and other != 'Unvote':
                latest_round.add_vote(Vote(requesting_player.player_id, other, time.time()))
            else:
                if other == 'Unvote':
                    latest_round.remove_vote(round_current_player_vote)
                else:
                    round_current_player_vote.choice = other
                    round_current_player_vote.timestamp = time.time()
        else:
            if round_current_player_vote is None:
                latest_round.add_vote(Vote(requesting_player.player_id, str(voted_player.player_id), time.time()))
            else:
                round_current_player_vote.choice = str(voted_player.player_id)
                round_current_player_vote.timestamp = time.time()

        await write_game(game, BASE_PATH)

        if voted_player is not None:
            success_vote_target = voted_player.player_discord_name
        else:
            success_vote_target = other
        await interaction.response.send_message(f'Registered vote for {success_vote_target}!', ephemeral=True)

@tree.command(name="vote-report",
              description="Generates a report of current voting totals",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def vote_report(interaction: discord.Interaction,
                      for_round: Optional[app_commands.Range[int, 0, 20]] = None,
                      with_history: Optional[Literal['Yes', 'No']] = 'No'):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    if not game.is_active:
        await interaction.response.send_message(f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    if for_round is None:
        report_round = game.get_latest_round()
    else:
        report_round = game.get_round(for_round)

    if report_round is None:
        await interaction.response.send_message(f'No active or matching round found for this game!', ephemeral=True)
        return

    vote_dict = {}

    for vote in report_round.votes:
        if vote.choice in vote_dict.keys():
            vote_dict.get(vote.choice).append(vote.player_id)
        else:
            vote_dict[vote.choice] = [vote.player_id]

    formatted_votes = f"**Vote Totals for round {report_round.round_number} as of <t:{int(time.time())}>**\n"
    formatted_votes += "```\n"
    for key, value in sorted(vote_dict.items(), key=lambda e: len(e[1]), reverse=True):
        if key == 'No Vote':
            formatted_votee = key
        else:
            formatted_votee = game.get_player(int(key)).player_discord_name
        formatted_votes += f"{formatted_votee}: {len(value)} vote(s)\n"
        formatted_votes += f"    Voted By: "
        for player_id in value:
            formatted_voter = game.get_player(int(player_id)).player_discord_name
            formatted_votes += f"{formatted_voter}, "
        formatted_votes = formatted_votes.rstrip(', ')
        formatted_votes += "\n"
    formatted_votes += "```\n"

    await interaction.response.send_message(formatted_votes, ephemeral=False)
    #With History to-be-implemented


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
