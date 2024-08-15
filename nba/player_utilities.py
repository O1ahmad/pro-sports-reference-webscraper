import argparse
import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import json
from bs4.element import Tag
from typing import Optional, List
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

def main(mongodb_url=None):
    players = get_player_list('a')
    
    if mongodb_url:
        print("Storing data in MongoDB...")
        collection_name = "nba_players"
        db_name = collection_name
        unique_properties = ["player", "birth_date"]  # List of properties to determine document uniqueness
        store_documents_in_mongodb(players, mongodb_url, db_name, collection_name, unique_properties)
    
    print(json.dumps(players, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Basketball Reference Webscraper")
    parser.add_argument("--mongodb-url", type=str, help="MongoDB connection string")

    args = parser.parse_args()
    main(args.mongodb_url)
