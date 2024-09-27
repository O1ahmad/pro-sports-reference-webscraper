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

def get_soup(response: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(response.text, 'html.parser')

def convert_height_to_inches(height: str) -> int:
    feet, inches = map(int, height.split('-'))
    return feet * 12 + inches

def get_stat_value(row: Tag, stat_name: str, is_text=True) -> Optional[str]:
    try:
        element = row.find('td', {'data-stat': stat_name})
        return element.text if is_text else element
    except AttributeError:
        # print(f"'{stat_name}' not found for row.")
        return None

def store_documents_in_mongodb(documents: list, mongodb_url: str, db_name: str, collection_name: str, unique_properties: List[str]):
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

def get_player_gamelog(player_link: str, season: str):
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

    while True:
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
                    if x == 'Not With Team' or x == 'Did Not Dress' or x == 'Inactive' or x == 'Injured Reserve':
                        inactive_game.append(i)
                except:
                    to_ignore.append(i)

            for i in range(len(table_rows)):
                if i not in to_ignore:
                    data = {}
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

            # Return log if successful
            return log

        except Exception as e:
            # Print error and retry after 10 seconds
            print(f"Error encountered while fetching {url}: {e}")

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

    while True:
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

            # Return players if successful
            return players

        except Exception as e:
            # Print error and retry after 10 seconds
            print(f"Error encountered while fetching {url}: {e}")

def find_missing_players_in_db(mongodb_url: str, last_initial: Optional[str] = None, player_name: Optional[str] = None):
    client = MongoClient(mongodb_url)
    db = client["nba_players"]
    collection = db["player_gamelogs"]

    missing_players = []

    # Open a log file to write missing players
    with open("missing_players.log", "w") as log_file:
        if player_name:
            # Extract the last name initial from the player's name
            last_name_initial = player_name.split()[-1][0].lower()
            print(f"Searching for player: {player_name} (last name initial '{last_name_initial}')")
            log_file.write(f"Searching for player: {player_name} (last name initial '{last_name_initial}')\n")

            # Search only in the corresponding last name initial
            players = get_player_list(last_name_initial)

            # Look for the player in the current list of players
            for player in players:
                if player['player'].lower() == player_name.lower():
                    print(f"Found player: {player['player']}")
                    log_file.write(f"Found player: {player['player']}\n")

                    # Check for missing years for this specific player
                    missing_years = []
                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        query = {
                            "player_link": player['link'],
                            "season": str(year)
                        }
                        existing_entry = collection.find_one(query)
                        if not existing_entry:
                            print(f"Player {player['player']} is missing for the season {year}")
                            log_file.write(f"Player {player['player']} is missing for the season {year}\n")
                            missing_years.append(year)

                    if missing_years:
                        missing_players.append({
                            "player": player['player'],
                            "link": player['link'],
                            "missing_years": missing_years
                        })
                    break
            else:
                print(f"Player {player_name} not found.")
                log_file.write(f"Player {player_name} not found.\n")

        else:
            # If a specific last initial is provided, use it; otherwise, scan A-Z
            initials = [last_initial.lower()] if last_initial else [chr(i) for i in range(ord('a'), ord('z') + 1)]
            
            for initial in initials:
                print(f"Scanning players with last name starting with '{initial}'")
                log_file.write(f"Scanning players with last name starting with '{initial}'\n")

                players = get_player_list(initial)

                # Iterate through each player and check for their presence in the database
                for player in players:
                    print(f"Checking player: {player['player']}")
                    log_file.write(f"Checking player: {player['player']}\n")

                    # Check for all seasons in which the player played
                    missing_years = []
                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        query = {
                            "player_link": player['link'],
                            "season": str(year)
                        }

                        # Check if the player and season exist in the database
                        existing_entry = collection.find_one(query)
                        if not existing_entry:
                            print(f"Player {player['player']} is missing for the season {year}")
                            log_file.write(f"Player {player['player']} is missing for the season {year}\n")
                            missing_years.append(year)

                    if missing_years:
                        missing_players.append({
                            "player": player['player'],
                            "link": player['link'],
                            "missing_years": missing_years
                        })

        # Print and log missing players and their missing seasons
    with open("missing_players_summary.log", "w") as result_file:
        if missing_players:
            print(f"{len(missing_players)} players missing in the database:")
            result_file.write(f"{len(missing_players)} players missing in the database:\n")
            for player in missing_players:
                print(f"Player: {player['player']}, Missing Years: {player['missing_years']}")
                result_file.write(f"Player: {player['player']}, Missing Years: {player['missing_years']}\n")
        else:
            print("No missing players found in the database.")
            result_file.write("No missing players found in the database.\n")

    return missing_players

def update_player_gamelogs_with_name(client: MongoClient, player_name: str, player_link: str):
    """
    Update all player gamelog documents with the player's name based on matching the 'player_link' field.
    """
    db = client["nba_players"]
    gamelog_collection = db["player_gamelogs"]

    # Update all documents in the player_gamelogs collection where player_link matches
    result = gamelog_collection.update_many(
        {"player_link": player_link},
        {"$set": {"player": player_name}}
    )

    print(f"Updated {result.modified_count} documents for player: {player_name}")

def update_all_players_gamelogs(mongodb_url: str):
    """
    Scan all player documents in the 'nba_players' collection and update the gamelogs with the player's name.
    """
    client = MongoClient(mongodb_url)
    db = client["nba_players"]
    players_collection = db["nba_players"]

    # Retrieve all players from the nba_players collection
    players = players_collection.find({})

    for player in players:
        player_name = player.get("player")
        player_link = player.get("link")

        if player_name and player_link:
            print(f"Updating gamelogs for player: {player_name}")
            update_player_gamelogs_with_name(client, player_name, player_link)

def add_missing_games_to_db(mongodb_url: str, player_name: Optional[str] = None, last_initial: Optional[str] = None):
    """
    Find and log missing game entries for players by comparing website data and MongoDB data. If missing game logs
    are found, they will be added to the database.

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

                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        season = str(year)
                        web_gamelogs = get_player_gamelog(player['link'], season)
                        db_gamelogs = list(collection.find({"player_link": player['link'], "season": season}))
                        db_game_dates = {entry['date_game'] for entry in db_gamelogs if 'date_game' in entry}

                        for game in web_gamelogs:
                            if game['date_game'] not in db_game_dates:
                                log_file.write(f"Missing game: Player: {player['player']}, Season: {season}, Date: {game['date_game']}\n")
                                missing_games.append(game)

                        # Insert missing games into the MongoDB collection
                        if missing_games:
                            store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
                            print(f"Added {len(missing_games)} missing games for player {player_name} to MongoDB.")
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
                    for year in range(int(player['year_min']), int(player['year_max']) + 1):
                        season = str(year)
                        web_gamelogs = get_player_gamelog(player['link'], season)
                        db_gamelogs = list(collection.find({"player_link": player['link'], "season": season}))
                        db_game_dates = {entry['date_game'] for entry in db_gamelogs if 'date_game' in entry}

                        for game in web_gamelogs:
                            if game['date_game'] not in db_game_dates:
                                log_file.write(f"Missing game: Player: {player['player']}, Season: {season}, Date: {game['date_game']}\n")
                                missing_games.append(game)

                        # Insert missing games into the MongoDB collection
                        if missing_games:
                            store_documents_in_mongodb(missing_games, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
                            print(f"Added {len(missing_games)} missing games for players with last name starting with '{initial.upper()}' to MongoDB.")
                if not missing_games:
                    log_file.write(f"No missing games found for players with last name starting with '{initial.upper()}'\n")

    if missing_games:
        print(f"Total missing games: {len(missing_games)}")
    else:
        print("No missing games found.")

    return missing_games

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
                        web_gamelogs = get_player_gamelog(player['link'], season)
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
                        web_gamelogs = get_player_gamelog(player['link'], season)
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
                    print(f"Total number of games found in MongoDB for players with last name starting with '{initial.upper()}': {total_games_in_db}")
                    print(f"Total number of games found on the web for players with last name starting with '{initial.upper()}': {total_games_on_web}")
                    log_file.write(f"Total number of games found in MongoDB for players with last name starting with '{initial.upper()}': {total_games_in_db}\n")
                    log_file.write(f"Total number of games found on the web for players with last name starting with '{initial.upper()}': {total_games_on_web}\n")

                    # Output missing games if there's a difference between web and MongoDB
                    if total_games_in_db != total_games_on_web:
                        total_missing_games = total_games_on_web - total_games_in_db
                        print(f"Total missing games for players with last name starting with '{initial.upper()}': {total_missing_games}")
                        log_file.write(f"Total missing games for players with last name starting with '{initial.upper()}': {total_missing_games}\n")

                if not missing_games:
                    log_file.write(f"No missing games found for players with last name starting with '{initial.upper()}'\n")

    if missing_games:
        print(f"Total missing games: {len(missing_games)}")
    else:
        print("No missing games found.")

    return missing_games


def main(mongodb_url: str, check_missing_players: Optional[str] = None):
    if check_missing_players:
        # Determine input format and handle accordingly
        if '-' in check_missing_players and len(check_missing_players) == 3:
            start, end = check_missing_players.split('-')
            initials = [chr(i) for i in range(ord(start.lower()), ord(end.lower()) + 1)]
            for initial in initials:
                add_missing_games_to_db(mongodb_url, last_initial=initial)

        elif ',' in check_missing_players:
            player_names = check_missing_players.split(',')
            for player_name in player_names:
                add_missing_games_to_db(mongodb_url, player_name=player_name.strip())

        elif len(check_missing_players) == 1:
            add_missing_games_to_db(mongodb_url, last_initial=check_missing_players.lower())

        else:
            add_missing_games_to_db(mongodb_url, player_name=check_missing_players)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, required=True, help="MongoDB connection string")
    parser.add_argument("--check-missing-players", type=str, help="Check and update missing game logs for a player (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant,Paul Pierce')")

    args = parser.parse_args()
    main(args.mongodb_url, args.check_missing_players)
