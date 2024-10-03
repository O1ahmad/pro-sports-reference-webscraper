import requests
import time

from utilities import get_stat_value, get_soup, convert_height_to_inches


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

def fetch_player_list(last_initial: str):
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
