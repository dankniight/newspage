# Simplified News Aggregator

A minimal news aggregator that fetches tech news from multiple sources and displays them in a clean web interface.

## Features

- Fetches news from 6 popular tech sources (The Verge, The Register, TechCrunch, Ars Technica, Wired, Engadget)
- Extracts article images when available
- Clean, responsive web interface with dark mode support
- Search and filter by source
- Automatic refresh every 30 minutes
- Manual refresh option

## Installation

1. Install required packages:
   ```
   pip install flask feedparser beautifulsoup4 requests schedule
   ```

2. Run the application:
   ```
   python news_app.py
   ```

3. Open your browser to `http://localhost:5000`

## Usage

- Browse articles on the main page
- Use the search box to find articles by keyword
- Filter by source using the dropdown
- Click "Refresh News" to manually fetch new articles
- Toggle dark mode using the icon in the top right corner

## How It Works

The application fetches RSS feeds from tech news sites every 30 minutes. It parses the articles, extracts images where possible, and stores them in a SQLite database. The Flask web interface displays the articles with pagination and filtering options.

Articles are only added to the database if they don't already exist (based on title), preventing duplicates.

## Deployment to GitHub Pages

This application is automatically deployed to GitHub Pages using GitHub Actions:

1. The workflow runs every 30 minutes to fetch new articles
2. Static files are generated using Frozen-Flask
3. The static files are deployed to the `gh-pages` branch
4. GitHub Pages serves the site from the `gh-pages` branch

To view the live site, visit: https://dankniight.github.io/newspage/