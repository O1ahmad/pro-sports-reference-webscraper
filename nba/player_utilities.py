import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import json

def get_soup(response: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(response.text, 'html.parser')

def convert_height_to_inches(height: str) -> int:
    feet, inches = map(int, height.split('-'))
    return feet * 12 + inches

def get_stat_value(row, stat_name: str, is_text=True):
    try:
        element = row.find('td', {'data-stat': stat_name})
        return element.text if is_text else element
    except AttributeError:
        print(f"'{stat_name}' not found for row.")
        return None

def get_player_list(last_initial: str):
    url = f'https://www.basketball-reference.com/players/{last_initial.lower()}/'
    page_content = get_soup(requests.get(url))

    players = []
    table_rows = page_content.find('tbody').find_all('tr')
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

    return players

def main():
    print(json.dumps(get_player_list('z'), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
