import requests
import time

from utilities import get_stat_value, get_soup, convert_height_to_inches

def get_player_averages(player_name: str, player_link: str):
    url = f'https://www.basketball-reference.com{player_link}.html'
    log = []

    try:
        response = requests.get(url)
        page_soup = get_soup(response)

        # Find game log table rows
        tables = page_soup.find_all('tbody')
        for i in range(len(tables)):
            type_id = tables[i].find('tr').get('id')
            if type_id and "playoff" in type_id:
                playoffs = True
            elif type_id:
                playoffs = False
            else:
                continue

            if type_id and "per_game" in type_id:
                type = "per_game"
            elif type_id and "totals" in type_id:
                type = "totals"
            elif type and "advanced" in type_id:
                type = "advanced"

            if type == "per_game" or type == "totals":
                for table_row in tables[i].find_all('tr'):
                    data = {}
                    data['player'] = player_name
                    data['player_link'] = player_link
                    data['type'] = type
                    data['playoffs'] = playoffs
                    data['season'] = table_row.get('th', {'data-stat': 'season'}).get('text') or table_row.find('th').text
                    data['age'] = get_stat_value(table_row, 'age')
                    data['team_id'] = get_stat_value(table_row, 'team_id')
                    data['lg_id'] = get_stat_value(table_row, 'lg_id')
                    data['games'] = get_stat_value(table_row, 'g')
                    data['games_started'] = get_stat_value(table_row, 'gs')
                    data['minutes_per_game'] = get_stat_value(table_row, 'mp_per_g') or get_stat_value(table_row, 'mp')
                    data['field_goals'] = get_stat_value(table_row, 'fg_per_g') or get_stat_value(table_row, 'fg')
                    data['field_goal_attempts'] = get_stat_value(table_row, 'fga_per_g') or get_stat_value(table_row, 'fga')
                    data['field_goal_percentage'] = get_stat_value(table_row, 'fg_pct')
                    data['3_point_field_goals'] = get_stat_value(table_row, 'fg3_per_g') or get_stat_value(table_row, 'fg3')
                    data['3_Point_field_goal_attempts'] = get_stat_value(table_row, 'fg3a_per_g') or get_stat_value(table_row, 'fg3a')
                    data['3_point_field_goal_percentage'] = get_stat_value(table_row, 'fg3_pct')
                    data['2_point_field_goals'] = get_stat_value(table_row, 'fg2_per_g') or get_stat_value(table_row, 'fg2')
                    data['2_point_field_goal_attempts'] = get_stat_value(table_row, 'fg2a_per_g') or get_stat_value(table_row, 'fg2a')
                    data['2_point_field_goal_percentage'] = get_stat_value(table_row, 'fg2_pct')
                    data['effective_field_goal_percentage'] = get_stat_value(table_row, 'efg_pct')
                    data['free_throws'] = get_stat_value(table_row, 'ft_per_g') or get_stat_value(table_row, 'ft')
                    data['free_throw_attempts'] = get_stat_value(table_row, 'fta_per_g') or get_stat_value(table_row, 'fta')
                    data['free_throw_percentage'] = get_stat_value(table_row, 'ft_pct')
                    data['offensive_rebounds'] = get_stat_value(table_row, 'orb_per_g') or get_stat_value(table_row, 'orb')
                    data['defensive_rebounds'] = get_stat_value(table_row, 'drb_per_g') or get_stat_value(table_row, 'drb')
                    data['total_rebounds'] = get_stat_value(table_row, 'trb_per_g') or get_stat_value(table_row, 'trb')
                    data['assists'] = get_stat_value(table_row, 'ast_per_g') or get_stat_value(table_row, 'ast')
                    data['steals'] = get_stat_value(table_row, 'stl_per_g') or get_stat_value(table_row, 'stl')
                    data['blocks'] = get_stat_value(table_row, 'blk_per_g') or get_stat_value(table_row, 'blk')
                    data['turnovers'] = get_stat_value(table_row, 'tov_per_g') or get_stat_value(table_row, 'tov')
                    data['personal_fouls'] = get_stat_value(table_row, 'pf_per_g') or get_stat_value(table_row, 'pf')
                    data['points'] = get_stat_value(table_row, 'pts_per_g') or get_stat_value(table_row, 'pts')
                    data['awards'] = get_stat_value(table_row, 'awards_summary') or get_stat_value(table_row, 'award_summary') or get_stat_value(table_row, 'awards') or get_stat_value(table_row, 'trp_dbl')

                    log.append(data)
            elif type == "advanced":
                for table_row in tables[i].find_all('tr'):
                    data = {}
                    data['player'] = player_name
                    data['player_link'] = player_link
                    data['type'] = type
                    data['playoffs'] = playoffs
                    data['season'] = table_row.get('th', {'data-stat': 'season'}).get('text') or table_row.find('th').text
                    data['age'] = get_stat_value(table_row, 'age')
                    data['team_id'] = get_stat_value(table_row, 'team_id')
                    data['lg_id'] = get_stat_value(table_row, 'lg_id')
                    data['games'] = get_stat_value(table_row, 'g')
                    data['minutes_per_game'] = get_stat_value(table_row, 'mp_per_g') or get_stat_value(table_row, 'mp')
                    data['per'] = get_stat_value(table_row, 'per')
                    data['true_shooting_percentage'] = get_stat_value(table_row, 'ts_pct')
                    data['fg3a_per_fga_pct'] = get_stat_value(table_row, 'fg3a_per_fga_pct')
                    data['fta_per_fga_pct'] = get_stat_value(table_row, 'fta_per_fga_pct')
                    data['orb_pct'] = get_stat_value(table_row, 'orb_pct')
                    data['drb_pct'] = get_stat_value(table_row, 'drb_pct')
                    data['trb_pct'] = get_stat_value(table_row, 'trb_pct')
                    data['ast_pct'] = get_stat_value(table_row, 'ast_pct')
                    data['stl_pct'] = get_stat_value(table_row, 'stl_pct')
                    data['blk_pct'] = get_stat_value(table_row, 'blk_pct')
                    data['tov_pct'] = get_stat_value(table_row, 'tov_pct')
                    data['usg_pct'] = get_stat_value(table_row, 'usg_pct')
                    data['ows'] = get_stat_value(table_row, 'ows')
                    data['dws'] = get_stat_value(table_row, 'dws')
                    data['ws'] = get_stat_value(table_row, 'ws')
                    data['ws_per_48'] = get_stat_value(table_row, 'ws_per_48')
                    data['obpm'] = get_stat_value(table_row, 'obpm')
                    data['dbpm'] = get_stat_value(table_row, 'dbpm')
                    data['bpm'] = get_stat_value(table_row, 'bpm')
                    data['vorp'] = get_stat_value(table_row, 'vorp')
                
                    log.append(data)
    except Exception as e:
        # Print error and retry after 10 seconds
        print(f"Error encountered while fetching {url}: {e}")

    return log

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
