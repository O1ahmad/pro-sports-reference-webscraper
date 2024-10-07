import argparse
import requests
from typing import Optional, List
from pymongo import MongoClient
import re

from utilities import get_stat_value, get_soup, convert_height_to_inches
from database_utils import handle_missing_players, handle_gamelog_name_add, store_documents_in_mongodb, handle_missing_player_averages
from webscrapers import get_player_gamelog, get_player_averages

def fetch_player_list(players_input: str, mongodb_url: Optional[str] = None) -> List[dict]:
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
            
            return players
        except Exception as e:
            print(f"Error querying MongoDB: {e}")

    # Fetch from web if not found in MongoDB
    for player_name in player_names:
        player_name = player_name.strip()
        initial = player_name.split()[-1][0].lower()
        url = f'{base_url}{initial}/'
        try:
            print(f"Fetching players from web for initial '{initial}'")
            response = requests.get(url)
            page_soup = get_soup(response)
            table_rows = page_soup.find('tbody').find_all('tr')

            for row in table_rows:
                name = row.find('th', {'data-stat': 'player'}).text.encode('latin1').decode('utf-8')
                if player_name not in name:
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

        except Exception as e:
            print(f"Error encountered while fetching {url}: {e}")
            return []
        
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

def fetch_player_gamelogs(mongodb_url: str, player_name: str, season: Optional[str] = None) -> List[dict]:
    """
    Retrieves player game logs from MongoDB if available, otherwise scrapes the data using the get_player_gamelog method.

    Args:
        mongodb_url (str): MongoDB connection string.
        player_name (str): The player's name.
        season (Optional[str]): The season to retrieve game logs for. If not provided, fetches all available seasons.

    Returns:
        List[dict]: A list of dictionaries containing game log data.
    """
    if mongodb_url:
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
            player = players_collection.find_one({"player": {"$regex": f"^{player_name}", "$options": "i"}})
            if not player:
                print(f"Player not found {player_name} in DB. Scraping from web...")
                player = fetch_players_by_name([player_name])[0]
    else:
        player = fetch_players_by_name([player_name])[0]
    
    # Scrape the data using get_player_gamelog if no data is found in MongoDB
    if season:
        logs = get_player_gamelog(player_name, player['link'], season)
        # Store the scraped data into MongoDB for future use
        if mongodb_url:
            store_documents_in_mongodb(logs, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
        return logs
    else:
        # If no season is provided, fetch all seasons the player played
        logs = []
        for year in range(int(player['year_min']), int(player['year_max']) + 1):
            logs_for_season = get_player_gamelog(player_name, player['link'], str(year))
            if mongodb_url:
                store_documents_in_mongodb(logs_for_season, mongodb_url, "nba_players", "player_gamelogs", ["player_link", "season", "game_season", "date_game"])
            logs.extend(logs_for_season)
        return logs

### Main Entrypoint ###

def main(mongodb_url: str,
         check_missing_players: Optional[str] = None,
         add_player_gamelog_names: Optional[str] = None, 
         fetch_players: Optional[str] = None, 
         fetch_gamelogs: Optional[str] = None,
         check_missing_averages: Optional[str] = None):
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

    if check_missing_averages:
        handle_missing_player_averages(mongodb_url, check_missing_averages)

    if add_player_gamelog_names:
        handle_gamelog_name_add(mongodb_url, add_player_gamelog_names)

    if fetch_players:
        players = fetch_player_list(fetch_players, mongodb_url)
        print(players)

    if fetch_gamelogs:
        # Parse player name and season if provided, separated by ":"
        parts = [part.strip() for part in fetch_gamelogs.split(':')]
        player_name = parts[0]
        season = parts[1] if len(parts) > 1 else None

        # Fetch player logs for the given player and optional season
        player_logs = fetch_player_gamelogs(mongodb_url, player_name, season)
        print(player_logs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, help="MongoDB connection string")
    parser.add_argument("--check-missing-players", type=str, help="Check and update missing game logs for a player (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant,Paul Pierce')")
    parser.add_argument("--check-missing-averages", type=str, help="Check and update missing season averages logs for a player (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant,Paul Pierce')")
    parser.add_argument("--add-player-gamelog-names", type=str, help="Add player names to gamelogs based on initials or player names (e.g. 'Kobe Bryant', 'a-c', 'b', 'Kobe Bryant, Paul Pierce')")
    parser.add_argument("--fetch-players", type=str, help="Fetch player information based on a name, list of names, initials, or a range of initials (e.g. 'Kobe Bryant', 'a-c', 'b')")
    parser.add_argument("--fetch-gamelogs", type=str, help="Fetch player game logs for the specified player and optional season (e.g., 'Kobe Bryant:2009')")

    args = parser.parse_args()
    main(args.mongodb_url, 
         args.check_missing_players, 
         args.add_player_gamelog_names, 
         args.fetch_players, 
         args.fetch_gamelogs,
         args.check_missing_averages)
