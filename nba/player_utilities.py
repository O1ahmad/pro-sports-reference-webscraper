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
        print(f"'{stat_name}' not found for row.")
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
    url = f'https://www.basketball-reference.com{player_link}/gamelog/{season}'
    page_soup = get_soup(requests.get(url))

    log = []
    table_rows = page_soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
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

    return log

def get_player_list(last_initial: str):
    url = f'https://www.basketball-reference.com/players/{last_initial.lower()}/'
    page_soup = get_soup(requests.get(url))
    players = []
    table_rows = page_soup.find('tbody').find_all('tr')
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
        #import pdb; pdb.set_trace()
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

    return players

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
        if missing_players:
            print(f"{len(missing_players)} players missing in the database:")
            log_file.write(f"{len(missing_players)} players missing in the database:\n")
            for player in missing_players:
                print(f"Player: {player['player']}, Missing Years: {player['missing_years']}")
                log_file.write(f"Player: {player['player']}, Missing Years: {player['missing_years']}\n")
        else:
            print("No missing players found in the database.")
            log_file.write("No missing players found in the database.\n")

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

def main(mongodb_url=None):
    if mongodb_url:
        # Update all player gamelogs with player names
        update_all_players_gamelogs(mongodb_url)

    all_gamelogs = []
    for initial in range(ord('g'), ord('l') + 1):
        last_initial = chr(initial)
        print(f"Processing players with last name starting with '{last_initial}'")
        players = get_player_list(last_initial)

        for player in players:
            print(f"Processing player: {player['player']}")
            for year in range(int(player['year_min']), int(player['year_max']) + 1):
                print(f"Processing year: {year}")
                gamelog = []
                try:
                    gamelog = get_player_gamelog(player['link'], str(year))
                except:
                    print(f"Error encountered while getting {player['link']} game log")
                    time.sleep(60)
                    continue

                all_gamelogs.extend(gamelog)
                if mongodb_url:
                    db_name = "nba_players"
                    collection_name = "player_gamelogs"
                    unique_properties = ["player_link", "season", "game_season", "date_game"]
                    store_documents_in_mongodb(gamelog, mongodb_url, db_name, collection_name, unique_properties)
                time.sleep(10)

    if mongodb_url:
        print("Storing data in MongoDB...")
        collection_name = "nba_players"
        db_name = collection_name
        unique_properties = ["player", "birth_date"]  # List of properties to determine document uniqueness
        store_documents_in_mongodb(players, mongodb_url, db_name, collection_name, unique_properties)

        collection_name = "player_gamelogs"
        unique_properties = ["player_link", "season", "game_season", "date_game"]
        store_documents_in_mongodb(all_gamelogs, mongodb_url, db_name, collection_name, unique_properties)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, help="MongoDB connection string")

    args = parser.parse_args()
    main(args.mongodb_url)
