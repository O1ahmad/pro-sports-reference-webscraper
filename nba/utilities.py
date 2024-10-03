import requests

from typing import Optional, List
from bs4 import BeautifulSoup, Tag


### Utility Methods ###

def get_soup(response: requests.Response) -> BeautifulSoup:
    """
    Parses an HTTP response into a BeautifulSoup object.

    Args:
        response (requests.Response): The HTTP response object obtained from a web request.

    Returns:
        BeautifulSoup: Parsed HTML content of the response.
    """
    return BeautifulSoup(response.text, 'html.parser')


def convert_height_to_inches(height: str) -> int:
    """
    Converts a player's height from feet-inches format to total inches.

    Args:
        height (str): A string representing the height in the format 'feet-inches' (e.g., '6-7').

    Returns:
        int: The height converted to inches.
    """
    feet, inches = map(int, height.split('-'))
    return feet * 12 + inches


def get_stat_value(row: Tag, stat_name: str, is_text: bool = True) -> Optional[str]:
    """
    Extracts the value of a specified stat from a row in an HTML table.

    Args:
        row (Tag): A BeautifulSoup Tag object representing a row of an HTML table.
        stat_name (str): The data-stat attribute name to search for in the table row.
        is_text (bool, optional): If True, returns the text value of the stat. If False, returns the Tag object. Defaults to True.

    Returns:
        Optional[str]: The text value of the specified stat if found, or None if the stat is not present.
    """
    try:
        element = row.find('td', {'data-stat': stat_name})
        return element.text if is_text else element
    except AttributeError:
        return None
