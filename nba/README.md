# 🏀 League of Leagues: Basketball Reference Webscraper 🏀

This Python application scrapes player data and game logs from [Basketball Reference](https://www.basketball-reference.com) and can optionally store the results in a MongoDB database. The application can fetch player data by last name initial or full player name, check for missing game logs, and add player names to game logs. 

MongoDB is **not required for all operations**; it serves as a caching and persistent storage option. If MongoDB is not used or available, the application will automatically fallback to querying and scraping the requested data directly from Basketball Reference.

## 🎯 Purpose

The purpose of this tool is to automate the extraction and organization of NBA player data from Basketball Reference. It supports the following actions:
- Fetches player information based on initials or full names.
- Checks if player game logs are missing in the MongoDB database.
- Can function without MongoDB by directly scraping data from Basketball Reference.

## 🚀 How to Run the Application

### 1. Install Dependencies

Make sure Python 3.x is installed on your system. Clone the repository and navigate to the project directory. Install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

**Dependencies include**:
- `requests` for making HTTP requests to Basketball Reference.
- `pandas` for data handling.
- `pymongo` for MongoDB database interaction (optional).
- `BeautifulSoup4` for parsing HTML data from Basketball Reference.

### 2. (Optional) Set Up MongoDB

MongoDB is **optional** but recommended if you want to persist and cache data locally for faster access in future queries. Ensure you have MongoDB running on your system or a remote MongoDB instance ready. You will need the MongoDB connection string (URI) to run the script. If you're using a local MongoDB instance, the connection string may look like this:

```bash
mongodb://localhost:27017
```

If you choose not to use MongoDB, the application will scrape the requested data from the Basketball Reference website.

### 3. Run the Application

The application provides several functionalities, each triggered using different flags. See the examples below for usage.

## Flags and Usage Examples

### `--mongodb-url` (Optional)
This flag specifies the MongoDB connection string. If not provided, the application will fallback to querying data from Basketball Reference directly. Use this flag if you want to cache data in MongoDB for faster future queries.

```bash
--mongodb-url "mongodb://localhost:27017"
```

### `--check-missing-players`
Checks the MongoDB database (if provided) or scrapes Basketball Reference for missing game logs for players. You can input:
- A **single player name** (e.g., `"Kobe Bryant"`).
- A **comma-separated list** of player names (e.g., `"Kobe Bryant, Paul Pierce"`).
- A **single last name initial** (e.g., `"b"`).
- A **range of last name initials** (e.g., `"a-c"`).

Example usage:

```bash
# Check for missing game logs for Kobe Bryant (with MongoDB)
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --check-missing-players "Kobe Bryant"

# Check for missing game logs for players whose last names start with 'b'
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --check-missing-players "b"

# Check for missing game logs for players with last name initials from 'a' to 'c'
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --check-missing-players "a-c"
```

### `--fetch-players`
Fetches player information from Basketball Reference based on the input. This flag accepts:
- A **single player name** (e.g., `"Kobe Bryant"`).
- A **comma-separated list** of player names (e.g., `"Kobe Bryant, Paul Pierce"`).
- A **single last name initial** (e.g., `"b"`).
- A **range of last name initials** (e.g., `"a-c"`).

Example usage:

```bash
# Fetch player information for Paul Pierce (with MongoDB)
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --fetch-players "Paul Pierce"

# Fetch player information for players whose last names start with 'p'
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --fetch-players "p"

# Fetch player information for players with last name initials from 'm' to 'z'
python nba/player_utilities.py --mongodb-url "mongodb://localhost:27017" --fetch-players "m-z"
```

### --fetch-player-gamelogs
Fetch game logs for a specific player and optionally for a specific season. The input should be in the format player_name:season. If the season is not provided, the method will fetch all available seasons for that player. The data is fetched from MongoDB if available, otherwise, it will be scraped from the web.

Example usage:

```bash
# Game logs for a single season
python nba/player_utilities.py --mongodb-url <mongo-url> --fetch-player-gamelogs "Kevin Garnett:2002" # With a season:
```

```bash
# Game log for all seasons
python nba/player_utilities.py --mongodb-url <mongo-url> --fetch-player-gamelogs "Amen Thompson" # Without a season:
```

## 📝 Contributing

Feel free to submit issues or contribute to the project by submitting a pull request! All contributions are welcome as we continue to improve the scraper.

## 🔧 Troubleshooting

- Ensure MongoDB is running and you have the correct connection string if you choose to use MongoDB.
- If MongoDB is not being used, ensure the Basketball Reference website is accessible for direct scraping.
