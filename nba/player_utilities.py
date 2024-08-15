import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests


def get_soup(response: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(response.text, 'html.parser')


def get_player_list(last_initial: str):
    url = f'https://www.basketball-reference.com/players/{last_initial.lower()}/'
    page_content = get_soup(requests.get(url))

    players = []
    table_rows = page_content.find('tbody').find_all('tr')
    for row in table_rows:
        data = {}
        data['player'] = row.find('th', {'data-stat': 'player'}).text
        data['year_min'] = row.find('td', {'data-stat': 'year_min'}).text
        data['year_max'] = row.find('td', {'data-stat': 'year_max'}).text
        data['pos'] = row.find('td', {'data-stat': 'pos'}).text
        data['height'] = row.find('td', {'data-stat': 'height'}).text
        data['weight'] = row.find('td', {'data-stat': 'weight'}).text
        data['birth_date'] = row.find('td', {'data-stat': 'birth_date'}).text
        data['colleges'] = row.find('td', {'data-stat': 'colleges'}).text

        players.append(data)

    return players

def main():
    print(get_player_list('A'))
    print(get_player_list('Z'))


if __name__ == '__main__':
    main()
