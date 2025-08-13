// This file will be used to generate news.json for the static site
const fs = require('fs');
const path = require('path');

// News data structure
const newsData = {
  articles: [],
  lastUpdated: new Date().toISOString()
};

// In a real implementation, this would fetch from RSS feeds
// For now, we'll save an empty structure that can be populated
fs.writeFileSync(path.join(__dirname, 'news.json'), JSON.stringify(newsData, null, 2));

console.log('News data file created');