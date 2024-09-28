# 🏆 League of Leagues: Pro Sports Reference Data Scrapers

This repository contains multiple web scraping tools for gathering player statistics and game logs from various professional sports reference websites, including:
- 🏀 **Basketball** (NBA) - [Basketball Reference](https://www.basketball-reference.com)
- 🏈 **Football** (NFL) - [Pro Football Reference](https://www.pro-football-reference.com)
- ⚾ **Baseball** (MLB) - [Baseball Reference](https://www.baseball-reference.com)
- 🏒 **Hockey** (NHL) - [Hockey Reference](https://www.hockey-reference.com)
- ⚽ **Soccer** (MLS) - [FBRef](https://fbref.com/en/) (Major League Soccer and other leagues)

These scrapers are designed to extract detailed statistics, player data, and game logs for each respective sport. They can either persist the data in a **MongoDB database** or directly scrape the information as needed.

## Features

- Scrapes **player data** and **game logs** from sports reference websites.
- Supports multiple sports including NBA, NFL, MLB, NHL, and MLS.
- Allows users to persist the scraped data into **MongoDB** for future queries.
- Each scraper is tailored to its respective sport's data structure and website.

## MongoDB Backend

For caching and persistent storage, the scrapers support **MongoDB**. MongoDB acts as a backend where scraped data is stored and queried. If MongoDB is not used, the scrapers will query data directly from the sports reference sites.

- Use MongoDB for **faster access** to already-scraped data.
- Perform **on-demand scraping** from sports reference websites when MongoDB is not available.

## Supported Scrapers

- [Basketball (NBA)](https://github.com/O1ahmad/pro-sports-reference-webscraper/tree/main/nba): Scrape player and game statistics from Pro Basketball Reference.

## Getting Started

Each sport-specific scraper contains its own README file, detailing how to:
1. Install the required dependencies.
2. Set up MongoDB (if used).
3. Run the scraper with appropriate flags and inputs for fetching and storing data.

You can check the individual README files in each scraper folder for specific instructions related to the sport you're interested in.

---

Stay tuned as we continue to expand support for more sports and enhance the scraping features! 😎⚽🏀⚾🏒🏈
