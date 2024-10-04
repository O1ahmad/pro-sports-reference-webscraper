import re
import json

from pymongo import MongoClient
from bson import json_util
from webscrapers import fetch_player_list, get_player_gamelog
from typing import Optional, List

### Database Helper Methods ###

def store_documents_in_mongodb(documents: list, mongodb_url: str, db_name: str, collection_name: str, unique_properties: List[str]):
    """
    Stores a list of documents into a MongoDB collection, ensuring that duplicates are avoided based on specified unique properties.

    Args:
        documents (list): A list of dictionaries representing the documents to be inserted into MongoDB.
        mongodb_url (str): MongoDB connection string (URL) to connect to the MongoDB instance.
        db_name (str): The name of the database where the documents will be stored.
        collection_name (str): The name of the collection within the database where the documents will be inserted.
        unique_properties (List[str]): A list of keys that define the uniqueness of each document. The function uses these keys to build a query to check for duplicates.

    Returns:
        None
    """
    client = MongoClient(mongodb_url)
    db = client[db_name]
    collection = db[collection_name]

    for document in documents:
        print(f"Storing document with unique properties: {unique_properties}")

        # Build the query using the list of unique properties
        query = {prop: document[prop] for prop in unique_properties if prop in document}

        try:
            existing_document = collection.find_one(query)
        except Exception as e:
            print(f"Error encountered accessing MongoDB: {str(e)}")
            existing_document = None

        if existing_document:
            print(f"Document with unique properties {query} found in MongoDB:")
            print(json.dumps(existing_document, indent=4, default=json_util.default))
        else:
            collection.insert_one(document)
            print(f"Document with unique properties {query} inserted into MongoDB")

def add_missing_games_to_db(mongodb_url: str, player_name: Optional[str] = None, last_initial: Optional[str] = None):
    """
    Find and log missing game entries for players by comparing website data and MongoDB data. If missing game logs
    are found, they will be added to the database. Outputs the total number of games found in MongoDB, in the web logs,
    and if there are missing games, outputs the total number of missing games and logs each missed game.

    Args:
        mongodb_url (str): MongoDB connection string.
        player_name (Optional[str]): The full name of the player to check.
        last_initial (Optional[str]): The initial of the player's last name (A-Z).
    """
    client = MongoClient(mongodb_url)
    db = client["nba_players"]
    collection = db["player_gamelogs"]
    missing_games = []

    with open("missed_games.log", "a") as log_file:
        if player_name:
            last_name_initial = player_name.split()[-1][0].lower()
            print(f"Searching for player: {player_name} (last name initial '{last_name_initial}')")
            log_file.write(f"Searching for player: {player_name} (last name initial '{last_name_initial}')\n")
            players = fetch_player_list(last_name_initial)

            for player in players:
                if player['player'].lower() == player_name.lower():
                    print(f"Found player: {player['player']}")
                    log_file.write(f"Found player: {player['player']}\n")

                    total_games_in_db = 0  # Counter for the total number of games found in MongoDB
                    total_games_on_web = 0  # Counter for the total number of games found on the web

                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        season = str(year)
                        web_gamelogs = get_player_gamelog(player['player'], player['link'], season)
                        db_gamelogs = list(collection.find({"player_link": player['link'], "season": season}))
                        db_game_dates = {entry['date_game'] for entry in db_gamelogs if 'date_game' in entry}

                        total_games_in_db += len(db_gamelogs)  # Update total games in DB for this player
                        total_games_on_web += len(web_gamelogs)  # Update total games found on the web for this player

                        for game in web_gamelogs:
                            if game['date_game'] not in db_game_dates:
                                log_file.write(f"Missing game: Player: {player['player']}, Season: {season}, Date: {game['date_game']}\n")
                                missing_games.append(game)
                    
                    # Output total games found in MongoDB and on the web
                    print(f"Total number of games found in MongoDB for player {player_name}: {total_games_in_db}")
                    print(f"Total number of games found on the web for player {player_name}: {total_games_on_web}")
                    log_file.write(f"Total number of games found in MongoDB for player {player_name}: {total_games_in_db}\n")
                    log_file.write(f"Total number of games found on the web for player {player_name}: {total_games_on_web}\n")

                    # Output missing games if there's a difference between web and MongoDB
                    if total_games_in_db != total_games_on_web:
                        total_missing_games = total_games_on_web - total_games_in_db
                        if total_missing_games != len(missing_games):
                            print("ERROR: total missing games counts do NOT match!")
                        print(f"Total missing games for player '{player['player']}': {total_missing_games}")
                        log_file.write(f"Total missing games for player {player_name}: {total_missing_games}\n")
                        print(f"Missing games count: {len(missing_games)}")
                        store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player", "season", "date_game"])
                        print(f"Added {len(missing_games)} missing games for player '{player['player']}' to MongoDB.")
                        missing_games.clear()
                    else:
                        print(f"No missing games found for player: {player['player']}\n")
                        log_file.write(f"No missing games found for player: {player['player']}\n")
                    break
            else:
                print(f"Player {player_name} not found.")
                log_file.write(f"Player {player_name} not found.\n")
        else:
            initials = [last_initial.lower()] if last_initial else [chr(i) for i in range(ord('a'), ord('z') + 1)]

            for initial in initials:
                print(f"Scanning players with last name starting with '{initial.upper()}'")
                players = fetch_player_list(initial)

                for player in players:
                    total_games_in_db = 0  # Counter for the total number of games found in MongoDB
                    total_games_on_web = 0  # Counter for the total number of games found on the web

                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        season = str(year)
                        web_gamelogs = get_player_gamelog(player['player'], player['link'], season)
                        db_gamelogs = list(collection.find({"player_link": player['link'], "season": season}))
                        db_game_dates = {entry['date_game'] for entry in db_gamelogs if 'date_game' in entry}

                        total_games_in_db += len(db_gamelogs)  # Update total games in DB for this player
                        total_games_on_web += len(web_gamelogs)  # Update total games found on the web for this player

                        for game in web_gamelogs:
                            if game['date_game'] not in db_game_dates:
                                log_file.write(f"Missing game: Player: {player['player']}, Season: {season}, Date: {game['date_game']}\n")
                                missing_games.append(game)

                    # Output total games found in MongoDB and on the web
                    print(f"Total number of games found in MongoDB for player '{player['player']}': {total_games_in_db}")
                    print(f"Total number of games found on the web for player '{player['player']}': {total_games_on_web}")
                    log_file.write(f"Total number of games found in MongoDB for player '{player['player']}': {total_games_in_db}\n")
                    log_file.write(f"Total number of games found on the web for player '{player['player']}': {total_games_on_web}\n")

                    # Output missing games if there's a difference between web and MongoDB
                    if total_games_in_db != total_games_on_web:
                        total_missing_games = total_games_on_web - total_games_in_db
                        if total_missing_games != len(missing_games):
                            print("ERROR: total missing games do NOT match!")
                        print(f"Total missing games for player '{player['player']}': {total_missing_games}")
                        log_file.write(f"Total missing games for player {player_name}: {total_missing_games}\n")
                        print(f"Missing games count: {len(missing_games)}")
                        store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player", "season", "date_game"])
                        print(f"Added {len(missing_games)} missing games for player: '{player['player']}' to MongoDB.")
                        missing_games.clear()
                    else:
                        print(f"No missing games found for player: {player['player']}\n")
                        log_file.write(f"No missing games found for player: {player['player']}\n")

    return missing_games

def handle_missing_players(mongodb_url: str, check_missing_players: Optional[str]):
    """
    Processes the 'check_missing_players' input and delegates the task to the appropriate
    logic based on whether initials, player names, or ranges of initials are provided.

    Args:
        mongodb_url (str): MongoDB connection string.
        check_missing_players (Optional[str]): Input string to specify the players or initials to check.
    """

    if re.match(r'^([a-zA-Z])-([a-zA-Z])$', check_missing_players):
        # Handle range of initials (e.g., 'a-c')
        start, end = check_missing_players.split('-')
        initials = [chr(i) for i in range(ord(start.lower()), ord(end.lower()) + 1)]
        for initial in initials:
            add_missing_games_to_db(mongodb_url, last_initial=initial)

    elif ',' in check_missing_players:
        # Handle comma-separated list of player names (e.g., 'Kobe Bryant, Paul Pierce')
        player_names = check_missing_players.split(',')
        for player_name in player_names:
            add_missing_games_to_db(mongodb_url, player_name=player_name.strip())

    elif re.match(r'^[a-zA-Z]$', check_missing_players):
        # Handle single initial (e.g., 'b')
        add_missing_games_to_db(mongodb_url, last_initial=check_missing_players.lower())

    # Handle specific player name (e.g., 'Kobe Bryant')
    add_missing_games_to_db(mongodb_url, player_name=check_missing_players)

def handle_gamelog_name_add(mongodb_url: str, players_input: Optional[str] = None):
    """
    Adds player names to the gamelogs based on input provided for players or initials.
    
    Args:
        mongodb_url (str): MongoDB connection string.
        players_input (Optional[str]): Input for players or initials to check (e.g. 'Kobe Bryant', 'a-c', 'b').
    """
    client = MongoClient(mongodb_url)
    db = client["nba_players"]
    players_collection = db["nba_players"]

    if re.match(r'^([a-zA-Z])-([a-zA-Z])$', players_input):
        # Handle range of initials (e.g., 'a-c')
        start, end = players_input.split('-')
        initials = [chr(i) for i in range(ord(start.lower()), ord(end.lower()) + 1)]
        for initial in initials:
            players = players_collection.find({"player": {"$regex": f"^{initial}", "$options": "i"}})
            process_player_gamelogs(client, players)

    elif ',' in players_input:
        # Handle comma-separated list of player names (e.g., 'Kobe Bryant, Paul Pierce')
        player_names = players_input.split(',')
        for player_name in player_names:
            players = players_collection.find({"player": player_name.strip()})
            process_player_gamelogs(client, players)

    elif re.match(r'^[a-zA-Z]$', players_input):
        # Handle single initial (e.g., 'b')
        players = players_collection.find({"player": {"$regex": f"^{players_input}", "$options": "i"}})
        process_player_gamelogs(client, players)

    # Handle specific player name (e.g., 'Kobe Bryant')
    players = players_collection.find({"player": players_input})
    process_player_gamelogs(client, players)

def process_player_gamelogs(client: MongoClient, player_data: List[dict]):
    """
    Processes and updates player gamelogs for a list of players.
    
    Args:
        client (MongoClient): The MongoDB client object.
        player_data (List[dict]): A list of player data containing 'player' and 'link' keys.
    """
    db = client["nba_players"]
    gamelog_collection = db["player_gamelogs"]

    for player in player_data:
        player_name = player.get("player")
        player_link = player.get("link")
        if player_name and player_link:
            # Remove asterisk from the player's name if present
            cleaned_player_name = player_name.replace('*', '').strip()

            print(f"Updating gamelogs for player: {cleaned_player_name}")

            # Update all documents in the player_gamelogs collection where player_link matches
            result = gamelog_collection.update_many(
                {"player_link": player_link},
                {"$set": {"player": cleaned_player_name}}
            )

            print(f"Updated {result.modified_count} documents for player: {cleaned_player_name}")
