# Simplified News Aggregator

A minimal news aggregator that fetches tech news from multiple sources and displays them in a clean web interface, now deployed to GitHub Pages.

## Features

- Fetches news from 5 popular tech sources (The Verge, The Register, TechCrunch, Ars Technica, Wired)
- Extracts article images when available
- Clean, responsive web interface with dark mode support
- Automatic updates every 30 minutes
- Manual refresh option

## How It Works

This is now a static site hosted on GitHub Pages:

1. A Python script (`generate_news.py`) fetches RSS feeds from tech news sites every 30 minutes via GitHub Actions
2. The script generates a `news.json` file with the latest articles
3. The static HTML file (`index.html`) fetches data from `news.json` and displays it with the same beautiful UI

## Deployment to GitHub Pages

This application is automatically deployed to GitHub Pages using GitHub Actions:

1. The workflow runs every 30 minutes to fetch new articles
2. A Python script generates a `news.json` file with the latest news
3. The static files (index.html, news.json, etc.) are deployed to the `gh-pages` branch
4. GitHub Pages serves the site from the `gh-pages` branch

To view the live site, visit: https://dankniight.github.io/newspage/

## Local Development

If you want to run the news fetching script locally:

1. Install required packages:
   ```
   pip install feedparser beautifulsoup4 requests
   ```

2. Run the news generation script:
   ```
   python generate_news.py
   ```

3. Open `index.html` in your browser

## Architecture

- **Frontend**: Static HTML/CSS/JavaScript (no frameworks)
- **Backend**: Python script that generates JSON data
- **Deployment**: GitHub Actions → GitHub Pages
- **Data**: JSON file updated every 30 minutes