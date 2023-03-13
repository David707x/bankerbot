#! banker_dom.py
# a class for managing game state details
import json
from typing import Optional
from datetime import datetime


class Player:
    def __init__(self, player_id: int, player_discord_name: str, faction_name: str, assets: int, tension: int, withdraw_limit: int = 2,
                 daily_withdraw_available: bool = True, is_faction_boss: bool = False, is_incarcerated: bool = False, is_dead: bool = False):
        self.player_id = player_id
        self.player_discord_name = player_discord_name
        self.faction_name = faction_name
        self.assets = assets
        self.tension = tension
        self.withdraw_limit = withdraw_limit
        self.daily_withdraw_available = daily_withdraw_available
        self.is_faction_boss = is_faction_boss
        self.is_incarcerated = is_incarcerated
        self.is_dead = is_dead

    def set_assets(self, assets: int):
        self.assets = assets

class Faction:
    def __init__(self, player_ids: [int], faction_name: str, assets: int):
        self.player_ids = player_ids
        self.faction_name = faction_name
        self.assets = assets

    def add_player(self, player_id: int):
        self.player_ids.append(player_id)

    def set_assets(self, assets: int):
        self.assets = assets

class Vote:
    def __init__(self, player_id: int, choice: str, timestamp: float):
        self.player_id = player_id
        self.choice = choice
        self.timestamp = timestamp

class Round:
    def __init__(self, votes: [Vote], round_number: int, is_active_round: bool):
        self.votes = votes
        self.round_number = round_number
        self.is_active_round = is_active_round

    def get_player_vote(self, player_id: int) -> Optional[Vote]:
        player_vote = None
        for vote in self.votes:
            if vote.player_id == player_id:
                player_vote = vote
        return player_vote

    def add_vote(self, vote: Vote):
        self.votes.append(vote)

    def remove_vote(self, vote: Vote):
        self.votes.remove(vote)

class Game:
    def __init__(self, is_active: bool, factions: [Faction], players: [Player], rounds: [Round]):
        self.is_active = is_active
        self.factions = factions
        self.players = players
        self.rounds = rounds

    def get_faction(self, faction_name: str) -> Optional[Faction]:
        for faction in self.factions:
            if faction.faction_name == faction_name:
                return faction
        return None

    def add_faction(self, faction: Faction):
        self.factions.append(faction)

    def get_player(self, player_id: int) -> Optional[Player]:
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def add_player(self, player: Player):
        self.players.append(player)

    def get_faction_of_player(self, player_id: int) -> Optional[Faction]:
        for faction in self.factions:
            if player_id in faction.player_ids:
                return faction
        return None

    def add_round(self, a_round: Round):
        self.rounds.append(a_round)

    def get_round(self, round_num: int) -> Optional[Round]:
        for a_round in self.rounds:
            if a_round.round_number == round_num:
                return a_round
        return None

    def get_latest_round(self) -> Optional[Round]:
        latest_round = None
        previous_round_num = 0
        for a_round in self.rounds:
            if a_round.round_number > previous_round_num:
                previous_round_num = a_round.round_number
                latest_round = a_round
        return latest_round

def read_json_to_dom(filepath: str) -> Game:
    with open(filepath, 'r') as openfile:
        json_object = json.load(openfile)

        is_active = json_object.get("is_active")
        factions = []
        players = []
        rounds = []
        if json_object.get("factions") is not None:
            for faction_entry in json_object.get("factions"):
                player_ids = []
                for player_id in faction_entry.get("player_ids"):
                    player_ids.append(player_id)
                faction_name = faction_entry.get("faction_name")
                assets = faction_entry.get("assets")
                factions.append(Faction(player_ids=player_ids,
                                        faction_name=faction_name,
                                        assets=assets))
        if json_object.get("players") is not None:
            for player_entry in json_object.get("players"):
                player_id = player_entry.get("player_id")
                player_discord_name = player_entry.get("player_discord_name")
                faction_name = player_entry.get("faction_name")
                withdraw_limit = player_entry.get("withdraw_limit")
                daily_withdraw_available = player_entry.get("daily_withdraw_available")
                is_incarcerated = player_entry.get("is_incarcerated")
                is_faction_boss = player_entry.get("is_faction_boss")
                is_dead = player_entry.get("is_dead")
                assets = player_entry.get("assets")
                tension = player_entry.get("tension")
                players.append(Player(player_id=player_id,
                                      player_discord_name=player_discord_name,
                                      faction_name=faction_name,
                                      assets=assets,
                                      tension=tension,
                                      withdraw_limit=withdraw_limit,
                                      daily_withdraw_available=daily_withdraw_available,
                                      is_faction_boss=is_faction_boss,
                                      is_incarcerated=is_incarcerated,
                                      is_dead=is_dead))

        if json_object.get("rounds") is not None:
            for round_entry in json_object.get("rounds"):
                round_num = round_entry.get("round_number")
                round_is_active = round_entry.get("is_active_round")
                votes = []
                if round_entry.get("votes") is not None:
                    for vote_entry in round_entry.get("votes"):
                        player_id = vote_entry.get("player_id")
                        choice = vote_entry.get("choice")
                        timestamp = vote_entry.get("timestamp")
                        votes.append(Vote(player_id=player_id,
                                          choice=choice,
                                          timestamp=timestamp))
                rounds.append(Round(round_number=round_num,
                                    is_active_round=round_is_active,
                                    votes=votes))

        return Game(is_active, factions, players, rounds)

def write_dom_to_json(game: Game, filepath: str):
    with open(filepath, 'w') as outfile:

        #convert Game to dictionary here
        game_dict = {"is_active": game.is_active}
        faction_dicts = []
        for faction in game.factions:
            faction_dicts.append({"player_ids": faction.player_ids,
                                  "faction_name": faction.faction_name,
                                  "assets": faction.assets
                                  })
        game_dict["factions"] = faction_dicts
        player_dicts = []
        for player in game.players:
            player_dicts.append({"player_id": player.player_id,
                                 "player_discord_name": player.player_discord_name,
                                 "faction_name": player.faction_name,
                                 "assets": player.assets,
                                 "tensions": player.tension,
                                 "withdraw_limit": player.withdraw_limit,
                                 "daily_withdraw_available": player.daily_withdraw_available,
                                 "is_faction_boss": player.is_faction_boss,
                                 "is_incarcerated": player.is_incarcerated,
                                 "is_dead": player.is_dead
                                 })
        game_dict["players"] = player_dicts
        round_dicts = []
        for a_round in game.rounds:
            vote_dicts = []
            for vote in a_round.votes:
                vote_dicts.append({"player_id": vote.player_id,
                                   "choice": vote.choice,
                                   "timestamp": vote.timestamp})
            round_dicts.append({"round_number": a_round.round_number,
                                "is_active_round": a_round.is_active_round,
                                "votes": vote_dicts})
        game_dict["rounds"] = round_dicts
        json.dump(game_dict, outfile, indent=2)

