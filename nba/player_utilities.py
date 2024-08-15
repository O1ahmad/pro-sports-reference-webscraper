import argparse
import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import json
from bs4.element import Tag
from typing import Optional
from pymongo import MongoClient
from bson import json_util

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

def get_player_list(last_initial: str, mongodb_url=None):
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

    db = None
    if mongodb_url:
        print("Storing data in mongodb...")
        client = MongoClient(mongodb_url)
        db = client.nba_players

        for p in players:
            print(f"Storing {p['player']}")
            try:
                existing_document = db.nba_players.find_one({"player": p['player']})
            except Exception as e:
                print(f"Error encountered accessing Mongo DB: {str(e)}")
                existing_document = None

            if existing_document:
                print(f"Document for {p['player']} found in MongoDB:")
                print(json.dumps(existing_document, indent=4, default=json_util.default))
            else:
                db.nba_players.insert_one(p)
                print(f"Results for {p['player']} inserted into MongoDB")

    return players

def main(mongodb_url=None):
    plist = get_player_list('b', mongodb_url)
    print(json.dumps(plist, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, help="MongoDB connection string")

    args = parser.parse_args()
    main(args.mongodb_url)
