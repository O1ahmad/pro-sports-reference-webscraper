import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import json

def get_soup(response: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(response.text, 'html.parser')

def convert_height_to_inches(height: str) -> int:
    feet, inches = map(int, height.split('-'))
    return feet * 12 + inches

def get_player_list(last_initial: str):
    url = f'https://www.basketball-reference.com/players/{last_initial.lower()}/'
    page_content = get_soup(requests.get(url))

    players = []
    table_rows = page_content.find('tbody').find_all('tr')
    for row in table_rows:
        data = {}
        data['player'] = row.find('th', {'data-stat': 'player'}).text
        data['link'] = row.find('a').get('href').replace('.html', '')
        data['year_min'] = row.find('td', {'data-stat': 'year_min'}).text
        data['year_max'] = row.find('td', {'data-stat': 'year_max'}).text
        data['pos'] = row.find('td', {'data-stat': 'pos'}).text
        data['height'] = row.find('td', {'data-stat': 'height'}).text
        data['height_inches'] = convert_height_to_inches(data['height'])
        data['weight'] = row.find('td', {'data-stat': 'weight'}).text
        data['birth_date'] = row.find('td', {'data-stat': 'birth_date'}).text
        data['colleges'] = row.find('td', {'data-stat': 'colleges'}).text
        try:
            data['college_link'] = row.find('td', {'data-stat': 'colleges'}).find('a').get('href')
        except:
            print("No college found!")

        players.append(data)

    return players

def main():
    print(json.dumps(get_player_list('z'), indent=2))

if __name__ == '__main__':
    main()
