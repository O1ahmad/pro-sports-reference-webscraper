import argparse
import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import json
from bs4.element import Tag
from typing import Optional, List
from pymongo import MongoClient
from bson import json_util
import time
import re

def get_soup(response: requests.Response) -> BeautifulSoup:
    """
    Parses an HTTP response into a BeautifulSoup object.

    Args:
        response (requests.Response): The HTTP response object obtained from a web request.

    Returns:
        BeautifulSoup: Parsed HTML content of the response.
    """
    return BeautifulSoup(response.text, 'html.parser')


def convert_height_to_inches(height: str) -> int:
    """
    Converts a player's height from feet-inches format to total inches.

    Args:
        height (str): A string representing the height in the format 'feet-inches' (e.g., '6-7').

    Returns:
        int: The height converted to inches.
    """
    feet, inches = map(int, height.split('-'))
    return feet * 12 + inches


def get_stat_value(row: Tag, stat_name: str, is_text: bool = True) -> Optional[str]:
    """
    Extracts the value of a specified stat from a row in an HTML table.

    Args:
        row (Tag): A BeautifulSoup Tag object representing a row of an HTML table.
        stat_name (str): The data-stat attribute name to search for in the table row.
        is_text (bool, optional): If True, returns the text value of the stat. If False, returns the Tag object. Defaults to True.

    Returns:
        Optional[str]: The text value of the specified stat if found, or None if the stat is not present.
    """
    try:
        element = row.find('td', {'data-stat': stat_name})
        return element.text if is_text else element
    except AttributeError:
        return None


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

def get_player_gamelog(player_name: str, player_link: str, season: str):
    """
    Fetches player game logs from Basketball Reference for a given season. Retries on failure.
    
    Args:
        player_link (str): The player's link on Basketball Reference.
        season (str): The season to fetch game logs for.

    Returns:
        log (list): A list of dictionaries containing game log data.
    """
    url = f'https://www.basketball-reference.com{player_link}/gamelog/{season}'
    log = []

    try:
        # Fetch the page and parse with BeautifulSoup
        response = requests.get(url)
        page_soup = get_soup(response)

        # Find game log table rows
        table_rows = page_soup.find('tbody').find_all('tr')

        # Handle inactive or DNP games
        inactive_game = []
        to_ignore = []
        for i in range(len(table_rows)):
            elements = table_rows[i].find_all('td')
            try:
                x = elements[len(elements) - 1].text
                if x == 'Injured Reserve' or x == 'Not With Team' or x == 'Did Not Dress' or x == 'Inactive' or x == 'Did Not Play':
                    inactive_game.append(i)
            except:
                to_ignore.append(i)

        for i in range(len(table_rows)):
            if i not in to_ignore:
                data = {}
                data['player'] = player_name
                data['player_link'] = player_link
                data['season'] = season
                data['game_season'] = get_stat_value(table_rows[i], 'game_season')
                data['date_game'] = get_stat_value(table_rows[i], 'date_game')
                data['age'] = get_stat_value(table_rows[i], 'age')
                data['team_id'] = get_stat_value(table_rows[i], 'team_id')
                data['game_location'] = get_stat_value(table_rows[i], 'game_location')
                data['opp_id'] = get_stat_value(table_rows[i], 'opp_id')
                data['game_result'] = get_stat_value(table_rows[i], 'game_result')
                if i not in inactive_game:
                    data['games_started'] = get_stat_value(table_rows[i], 'gs')
                    data['minutes_played'] = get_stat_value(table_rows[i], 'mp')
                    data['field_goals'] = get_stat_value(table_rows[i], 'fg')
                    data['field_goals_attempted'] = get_stat_value(table_rows[i], 'fga')
                    data['field_goal_percentage'] = get_stat_value(table_rows[i], 'fg_pct')
                    data['3point_field_goals'] = get_stat_value(table_rows[i], 'fg3')
                    data['3point_field_goals_attempted'] = get_stat_value(table_rows[i], 'fg3a')
                    data['3point_field_goal_percentage'] = get_stat_value(table_rows[i], 'fg3_pct')
                    data['free_throws'] = get_stat_value(table_rows[i], 'ft')
                    data['free_throws_attempted'] = get_stat_value(table_rows[i], 'fta')
                    data['free_throw_percentage'] = get_stat_value(table_rows[i], 'ft_pct')
                    data['offensive_rebounds'] = get_stat_value(table_rows[i], 'orb')
                    data['defensive_rebounds'] = get_stat_value(table_rows[i], 'drb')
                    data['total_rebounds'] = get_stat_value(table_rows[i], 'trb')
                    data['assists'] = get_stat_value(table_rows[i], 'ast')
                    data['steals'] = get_stat_value(table_rows[i], 'stl')
                    data['blocks'] = get_stat_value(table_rows[i], 'blk')
                    data['turnovers'] = get_stat_value(table_rows[i], 'tov')
                    data['personal_fouls'] = get_stat_value(table_rows[i], 'pf')
                    data['points'] = get_stat_value(table_rows[i], 'pts')
                    data['game_score'] = get_stat_value(table_rows[i], 'game_score')
                    data['plus_minus'] = get_stat_value(table_rows[i], 'plus_minus')
                else:
                    data['status'] = "Inactive"

                log.append(data)

        print(f"Processing player link: {player_link}, season: {season}")
        time.sleep(5)

    except Exception as e:
        # Print error and retry after 10 seconds
        print(f"Error encountered while fetching {url}: {e}")

    return log

def get_player_list(last_initial: str):
    """
    Fetches the list of players whose last names start with the specified initial from Basketball Reference.
    Retries on failure.

    Args:
        last_initial (str): The first letter of the players' last names.

    Returns:
        players (list): A list of dictionaries containing player data.
    """
    url = f'https://www.basketball-reference.com/players/{last_initial.lower()}/'
    players = []

    try:
        # Fetch the page and parse with BeautifulSoup
        response = requests.get(url)
        page_soup = get_soup(response)

        # Find player table rows
        table_rows = page_soup.find('tbody').find_all('tr')

        # Extract player data
        for row in table_rows:
            data = {}
            data['player'] = row.find('th', {'data-stat': 'player'}).text.encode('latin1').decode('utf-8')
            data['link'] = row.find('a').get('href').replace('.html', '')
            data['year_min'] = get_stat_value(row, 'year_min')
            data['year_max'] = get_stat_value(row, 'year_max')
            data['pos'] = get_stat_value(row, 'pos')
            data['height'] = get_stat_value(row, 'height')
            data['height_inches'] = convert_height_to_inches(data['height']) if data['height'] else None
            data['weight'] = get_stat_value(row, 'weight')
            data['birth_date'] = get_stat_value(row, 'birth_date')
            data['colleges'] = get_stat_value(row, 'colleges')

            # Try to get the college link if it exists
            college_element = get_stat_value(row, 'colleges', is_text=False)
            if college_element:
                try:
                    data['college_link'] = college_element.find('a').get('href')
                except AttributeError:
                    print(f"College link not found for {data['player']}")

            players.append(data)

    except Exception as e:
        # Print error and retry after 10 seconds
            print(f"Error encountered while fetching {url}: {e}")

    return players

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
            players = get_player_list(last_name_initial)

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

                        # Insert missing games into the MongoDB collection
                        if missing_games:
                            store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
                            print(f"Added {len(missing_games)} missing games for player {player_name} to MongoDB.")
                    
                    # Output total games found in MongoDB and on the web
                    print(f"Total number of games found in MongoDB for player {player_name}: {total_games_in_db}")
                    print(f"Total number of games found on the web for player {player_name}: {total_games_on_web}")
                    log_file.write(f"Total number of games found in MongoDB for player {player_name}: {total_games_in_db}\n")
                    log_file.write(f"Total number of games found on the web for player {player_name}: {total_games_on_web}\n")

                    # Output missing games if there's a difference between web and MongoDB
                    if total_games_in_db != total_games_on_web:
                        total_missing_games = total_games_on_web - total_games_in_db
                        print(f"Total missing games for player {player_name}: {total_missing_games}")
                        log_file.write(f"Total missing games for player {player_name}: {total_missing_games}\n")

                    if not missing_games:
                        log_file.write(f"No missing games found for player: {player_name}\n")
                    break
            else:
                print(f"Player {player_name} not found.")
                log_file.write(f"Player {player_name} not found.\n")
        else:
            initials = [last_initial.lower()] if last_initial else [chr(i) for i in range(ord('a'), ord('z') + 1)]

            for initial in initials:
                print(f"Scanning players with last name starting with '{initial.upper()}'")
                players = get_player_list(initial)

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

                        # Insert missing games into the MongoDB collection
                        if missing_games:
                            store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
                            print(f"Added {len(missing_games)} missing games for players with last name starting with '{initial.upper()}' to MongoDB.")

                    # Output total games found in MongoDB and on the web
                    print(f"Total number of games found in MongoDB for player '{player['player']}': {total_games_in_db}")
                    print(f"Total number of games found on the web for player '{player['player']}': {total_games_on_web}")
                    log_file.write(f"Total number of games found in MongoDB for player '{player['player']}': {total_games_in_db}\n")
                    log_file.write(f"Total number of games found on the web for player '{player['player']}': {total_games_on_web}\n")

                    # Output missing games if there's a difference between web and MongoDB
                    if total_games_in_db != total_games_on_web:
                        total_missing_games = total_games_on_web - total_games_in_db
                        print(f"Total missing games for player '{player['player']}': {total_missing_games}")
                        log_file.write(f"Total missing games for player '{player['player']}': {total_missing_games}\n")

                if not missing_games:
                    log_file.write(f"No missing games found for players with last name starting with '{initial.upper()}'\n")

    if missing_games:
        print(f"Total missing games: {len(missing_games)}")
    else:
        print("No missing games found.")

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

def get_player_list(players_input: str, mongodb_url: Optional[str] = None) -> List[dict]:
    """
    Fetches the list of players based on input. The input can be:
    - A single player name
    - A comma-separated list of player names
    - A single last name initial
    - A range of last name initials (e.g., 'a-c')

    Args:
        players_input (str): The player input string (single name, list, initial, or initial range).
        mongodb_url (Optional[str]): MongoDB connection string for checking the database.

    Returns:
        List[dict]: A list of dictionaries containing player data.
    """
    base_url = 'https://www.basketball-reference.com/players/'
    players = []

    if re.match(r'^([a-zA-Z])-([a-zA-Z])$', players_input):
        # Handle range of initials (e.g., 'a-c')
        start, end = players_input.split('-')
        initials = [chr(i) for i in range(ord(start.lower()), ord(end.lower()) + 1)]
    elif ',' in players_input:
        # Handle comma-separated list of player names (e.g., 'Kobe Bryant, Paul Pierce')
        player_names = players_input.split(',')
        return fetch_players_by_name(player_names, mongodb_url)
    elif re.match(r'^[a-zA-Z]$', players_input):
        # Handle single initial (e.g., 'b')
        initials = [players_input.lower()]
    else:
        # Handle single player name (e.g., 'Kobe Bryant')
        return fetch_players_by_name([players_input], mongodb_url)

    # Fetch players based on initials
    for initial in initials:
        url = f'{base_url}{initial}/'
        players.extend(fetch_players_by_initial(url, initial, mongodb_url=mongodb_url))

    return players


def fetch_players_by_name(player_names: List[str], mongodb_url: Optional[str] = None) -> List[dict]:
    """
    Fetches players based on a list of player names, checking MongoDB first before web requests.

    Args:
        player_names (List[str]): List of player names.
        mongodb_url (Optional[str]): MongoDB connection string for checking the database.

    Returns:
        List[dict]: A list of dictionaries containing player data.
    """
    players = []
    base_url = 'https://www.basketball-reference.com/players/'

    if mongodb_url:
        try:
            client = MongoClient(mongodb_url)
            db = client["nba_players"]
            players_collection = db["nba_players"]

            for player_name in player_names:
                # Use a regex to match player names even if the MongoDB entry contains extra characters like an asterisk
                mongo_players = list(players_collection.find({"player": {"$regex": f"^{player_name.strip()}", "$options": "i"}}, {"_id": 0}))
                if mongo_players:
                    print(f"Player '{player_name.strip()}' found in MongoDB")
                    players.extend(mongo_players)
                else:
                    # Fetch from web if not found in MongoDB
                    initial = player_name.strip().split()[-1][0].lower()
                    url = f'{base_url}{initial}/'
                    try:
                        print(f"Fetching players from web for initial '{initial}'")
                        response = requests.get(url)
                        page_soup = get_soup(response)
                        table_rows = page_soup.find('tbody').find_all('tr')

                        for row in table_rows:
                            name = row.find('th', {'data-stat': 'player'}).text.encode('latin1').decode('utf-8')
                            if player_name != name:
                                continue

                            data = {
                                'player': player_name,
                                'link': row.find('a').get('href').replace('.html', ''),
                                'year_min': get_stat_value(row, 'year_min'),
                                'year_max': get_stat_value(row, 'year_max'),
                                'pos': get_stat_value(row, 'pos'),
                                'height': get_stat_value(row, 'height'),
                                'height_inches': convert_height_to_inches(get_stat_value(row, 'height')) if get_stat_value(row, 'height') else None,
                                'weight': get_stat_value(row, 'weight'),
                                'birth_date': get_stat_value(row, 'birth_date'),
                                'colleges': get_stat_value(row, 'colleges')
                            }

                            college_element = get_stat_value(row, 'colleges', is_text=False)
                            if college_element:
                                try:
                                    data['college_link'] = college_element.find('a').get('href')
                                except AttributeError:
                                    print(f"College link not found for {data['player']}")

                            players.append(data)

                        return players

                    except Exception as e:
                        print(f"Error encountered while fetching {url}: {e}")
                        return []

        except Exception as e:
            print(f"Error querying MongoDB: {e}")

    return players


def fetch_players_by_initial(url: str, initial: str, mongodb_url: Optional[str] = None) -> List[dict]:
    """
    Fetches players whose last names start with the given initial or matches a specific player name.
    It first checks the MongoDB database (if `mongodb_url` is provided) before making a web request.

    Args:
        url (str): The URL to fetch players by initial.
        specific_name (Optional[str]): Specific player name to search for.
        mongodb_url (Optional[str]): MongoDB connection string for checking the database.

    Returns:
        List[dict]: A list of dictionaries containing player data.
    """
    players = []

    if mongodb_url:
        try:
            client = MongoClient(mongodb_url)
            db = client["nba_players"]
            players_collection = db["nba_players"]

            mongo_players = list(players_collection.find({"player": {"$regex": f"^{initial}", "$options": "i"}}, {"_id": 0}))
            if mongo_players:
                print(f"Players found in MongoDB for initial '{initial}': {len(mongo_players)}")
                return mongo_players  # Return the players from MongoDB if found

        except Exception as e:
            print(f"Error querying MongoDB: {e}")

    # If MongoDB check fails or no data found, make a web request
    try:
        print(f"Fetching players from web for initial '{initial}'")
        response = requests.get(url)
        page_soup = get_soup(response)
        table_rows = page_soup.find('tbody').find_all('tr')

        for row in table_rows:
            player_name = row.find('th', {'data-stat': 'player'}).text.encode('latin1').decode('utf-8')
            data = {
                'player': player_name,
                'link': row.find('a').get('href').replace('.html', ''),
                'year_min': get_stat_value(row, 'year_min'),
                'year_max': get_stat_value(row, 'year_max'),
                'pos': get_stat_value(row, 'pos'),
                'height': get_stat_value(row, 'height'),
                'height_inches': convert_height_to_inches(get_stat_value(row, 'height')) if get_stat_value(row, 'height') else None,
                'weight': get_stat_value(row, 'weight'),
                'birth_date': get_stat_value(row, 'birth_date'),
                'colleges': get_stat_value(row, 'colleges')
            }

            college_element = get_stat_value(row, 'colleges', is_text=False)
            if college_element:
                try:
                    data['college_link'] = college_element.find('a').get('href')
                except AttributeError:
                    print(f"College link not found for {data['player']}")

            players.append(data)

        return players

    except Exception as e:
        print(f"Error encountered while fetching {url}: {e}")
        return []

def get_player_gamelogs(mongodb_url: str, player_name: str, season: Optional[str] = None) -> List[dict]:
    """
    Retrieves player game logs from MongoDB if available, otherwise scrapes the data using the get_player_gamelog method.

    Args:
        mongodb_url (str): MongoDB connection string.
        player_name (str): The player's name.
        season (Optional[str]): The season to retrieve game logs for. If not provided, fetches all available seasons.

    Returns:
        List[dict]: A list of dictionaries containing game log data.
    """
    client = MongoClient(mongodb_url)
    db = client["nba_players"]
    gamelog_collection = db["player_gamelogs"]

    # Try to find the player's game logs in MongoDB
    query = {"player": {"$regex": f"^{player_name}", "$options": "i"}}
    if season:
        query["season"] = season

    player_logs = list(gamelog_collection.find(query, {"_id": 0}))

    if player_logs:
        print(f"Game logs found in MongoDB for player {player_name} in season {season if season else 'all seasons'}")
        return player_logs
    else:
        print(f"No game logs found in MongoDB for player {player_name}. Scraping data...")

        # Get player details from MongoDB (to retrieve the player_link for scraping)
        players_collection = db["nba_players"]
        player_doc = players_collection.find_one({"player": {"$regex": f"^{player_name}", "$options": "i"}})

        if not player_doc:
            print(f"Player {player_name} not found in the database.")
            return []

        player_link = player_doc.get("link")
        if not player_link:
            print(f"Player link not found for {player_name}.")
            return []

        # Scrape the data using get_player_gamelog if no data is found in MongoDB
        if season:
            logs = get_player_gamelog(player_name, player_link, season)
            # Store the scraped data into MongoDB for future use
            store_documents_in_mongodb(logs, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
            return logs
        else:
            # If no season is provided, fetch all seasons the player played
            logs = []
            for year in range(int(player_doc['year_min']), int(player_doc['year_max']) + 1):
                logs_for_season = get_player_gamelog(player_name, player_link, str(year))
                store_documents_in_mongodb(logs_for_season, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
                logs.extend(logs_for_season)
            return logs

def main(mongodb_url: str,
         check_missing_players: Optional[str] = None,
         add_player_gamelog_names: Optional[str] = None, 
         fetch_players_input: Optional[str] = None, 
         fetch_player_gamelogs: Optional[str] = None):
    """
    Main entry point for the script. Delegates to different functions based on the input.

    Args:
        mongodb_url (str): MongoDB connection string.
        check_missing_players (Optional[str]): Input string to specify the players or initials to check for missing game logs.
        add_player_gamelog_names (Optional[str]): Input string to specify the players or initials to update gamelogs with player names.
        fetch_players_input (Optional[str]): Input string to specify the players or initials to fetch.
        fetch_player_gamelogs (Optional[str]): Input string to specify the player and optional season (e.g., 'Kobe Bryant:2009').
    """
    if check_missing_players:
        handle_missing_players(mongodb_url, check_missing_players)

    if add_player_gamelog_names:
        handle_gamelog_name_add(mongodb_url, add_player_gamelog_names)

    if fetch_players_input:
        players = get_player_list(fetch_players_input, mongodb_url)
        print(players)

    if fetch_player_gamelogs:
        # Parse player name and season if provided, separated by ":"
        parts = [part.strip() for part in fetch_player_gamelogs.split(':')]
        player_name = parts[0]
        season = parts[1] if len(parts) > 1 else None

        # Fetch player logs for the given player and optional season
        player_logs = get_player_gamelogs(mongodb_url, player_name, season)
        print(player_logs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, required=True, help="MongoDB connection string")
    parser.add_argument("--check-missing-players", type=str, help="Check and update missing game logs for a player (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant,Paul Pierce')")
    parser.add_argument("--add-player-gamelog-names", type=str, help="Add player names to gamelogs based on initials or player names (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant, Paul Pierce')")
    parser.add_argument("--fetch-players", type=str, help="Fetch player information based on a name, list of names, initials, or a range of initials (e.g. 'Kobe Bryant', 'a-c', 'b')")
    parser.add_argument("--fetch-player-gamelogs", type=str, help="Fetch player game logs for the specified player and optional season (e.g., 'Kobe Bryant:2009')")

    args = parser.parse_args()
    main(args.mongodb_url, 
         args.check_missing_players, 
         args.add_player_gamelog_names, 
         args.fetch_players, 
         args.fetch_player_gamelogs)
