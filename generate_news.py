import feedparser
from datetime import datetime, timezone, timedelta
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import requests
import json
import os
from collections import defaultdict

# Tech news RSS feeds with clean source names
RSS_FEEDS = {
    'https://www.theverge.com/rss/index.xml': 'The Verge',
    'https://www.theregister.com/headlines.atom': 'The Register',
    'https://techcrunch.com/feed/': 'TechCrunch',
    'https://feeds.arstechnica.com/arstechnica/index': 'Ars Technica',
    'https://www.wired.com/feed/rss': 'Wired'
}

# Sources that typically don't include images in their feeds and need article page fetching
SOURCES_REQUIRING_PAGE_FETCH = {'TechCrunch', 'The Register'}

# Phrases to filter out from article titles and summaries
FILTERED_PHRASES = [
    'advertisement',
    'sponsored',
    'promo',
    'deal',
    'offer',
    'discount',
    'sale',
    'buy now',
    'shop now',
    'limited time',
    'free trial',
    'sign up',
    'subscribe'
]

def extract_image_from_article_page(article_url, source):
    """Extract the main image from an article page for specific sources"""
    try:
        # Only fetch pages for sources known to not include images in feeds
        if source not in SOURCES_REQUIRING_PAGE_FETCH:
            return None
            
        print(f"Fetching article page for image: {article_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Source-specific selectors for finding the main image
        if source == 'TechCrunch':
            # Check meta tags for og:image (often the best source)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            # Look for featured image containers
            featured_image_container = (
                soup.find('div', class_='article__featured-image') or
                soup.find('div', class_='featured-image') or
                soup.find('div', {'data-attribute': 'article-featured-image'})
            )
            
            if featured_image_container:
                img_tag = featured_image_container.find('img')
                if img_tag and img_tag.get('src'):
                    return img_tag['src']
        
        elif source == 'The Register':
            # Method 1: Check meta tags for og:image (often the best source)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                src = og_image['content']
                # Skip ad images
                if not ('doubleclick.net' in src or 'amazon-adsystem' in src):
                    return src
            
            # Method 2: Look for images in the article body
            article_body = soup.find('div', id='body')
            if article_body:
                # Find all images in the article body
                img_tags = article_body.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        # Skip ad images
                        if 'doubleclick.net' in src or 'amazon-adsystem' in src:
                            continue
                        # Prefer larger images
                        width = img.get('width')
                        if width and width.isdigit() and int(width) > 300:
                            return src
                        # Or just return the first non-ad image if no width attribute
                        elif not width:
                            return src
        
        # Generic fallback: look for meta tags or first large image
        if not source in ['TechCrunch', 'The Register']:  # Only for other sources
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            # Find all images and pick the first large one
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Check if it's a large image
                    width = img.get('width')
                    if width and width.isdigit() and int(width) > 300:
                        return src
        
        return None
        
    except Exception as e:
        print(f"Error fetching article image from page {article_url}: {e}")
        return None

def extract_images_from_entry(entry, feed_url, source):
    """Extract and validate image URLs from an entry with multiple fallback methods"""
    image_url = None
    tried_urls = set()  # To prevent duplicates
    
    # Method 1: Check for media content (often higher quality)
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if hasattr(media, 'url') and media.get('type', '').startswith('image'):
                img_url = media.url
                if img_url and img_url not in tried_urls:
                    tried_urls.add(img_url)
                    # Prefer larger images if available
                    if not image_url or (media.get('width', 0) > 300):
                        image_url = img_url
    
    # Method 2: Check for media thumbnails
    if not image_url and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            if thumb.get('url'):
                img_url = thumb['url']
                if img_url and img_url not in tried_urls:
                    tried_urls.add(img_url)
                    image_url = img_url
                    break  # Take the first valid one
    
    # Method 3: Check for enclosures
    if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            if hasattr(enclosure, 'href') and enclosure.get('type', '').startswith('image'):
                img_url = enclosure.href
                if img_url and img_url not in tried_urls:
                    tried_urls.add(img_url)
                    image_url = img_url
                    break
    
    # Method 4: Try to extract from content HTML (especially for The Verge)
    if not image_url and hasattr(entry, 'content'):
        for content in entry.content:
            if 'value' in content:
                try:
                    soup = BeautifulSoup(content['value'], 'html.parser')
                    img_tags = soup.find_all('img')
                    for img in img_tags:
                        src = img.get('src') or img.get('data-src')  # Also check for lazy-loaded images
                        if src:
                            # Convert relative URLs to absolute
                            full_url = urljoin(feed_url, src)
                            if full_url not in tried_urls:
                                tried_urls.add(full_url)
                                # Skip tiny placeholder images
                                width = img.get('width')
                                if width and str(width).isdigit() and int(width) < 50:
                                    continue
                                image_url = full_url
                                break  # Take the first good one
                except Exception as e:
                    print(f"Error parsing content HTML: {e}")
    
    # Method 5: Try to extract from summary HTML
    if not image_url and hasattr(entry, 'summary'):
        try:
            soup = BeautifulSoup(entry.summary, 'html.parser')
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src')  # Also check for lazy-loaded images
                if src:
                    # Convert relative URLs to absolute
                    full_url = urljoin(feed_url, src)
                    if full_url not in tried_urls:
                        tried_urls.add(full_url)
                        # Skip tiny placeholder images
                        width = img.get('width')
                        if width and str(width).isdigit() and int(width) < 50:
                            continue
                        image_url = full_url
                        break  # Take the first good one
        except Exception as e:
            print(f"Error parsing summary HTML: {e}")
    
    # Method 6: Fetch article page for sources that don't include images in feeds
    if not image_url and source in SOURCES_REQUIRING_PAGE_FETCH:
        image_url = extract_image_from_article_page(entry.link, source)
    
    # Handle protocol-relative URLs
    if image_url and image_url.startswith('//'):
        image_url = 'https:' + image_url
        
    return image_url

def should_filter_article(title, summary):
    """Check if an article should be filtered out based on its title or summary"""
    text = (title + " " + summary).lower()
    for phrase in FILTERED_PHRASES:
        if phrase in text:
            return True
    return False

def parse_date(date_str):
    """Parse date string and return datetime object"""
    if not date_str:
        return datetime.now(timezone.utc)
    
    try:
        # Try to parse with timezone info
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt
    except ValueError:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
            return dt
        except ValueError:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                # Assume UTC if no timezone info
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                # If all else fails, use current time
                return datetime.now(timezone.utc)

def fetch_articles():
    articles = []
    source_article_count = defaultdict(int)
    
    # Fetch more articles per source to increase variety
    articles_per_source = 30
    
    # Only include articles from the last 48 hours
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=48)
    
    for feed_url, clean_source_name in RSS_FEEDS.items():
        try:
            print(f"Fetching from {clean_source_name}...")
            feed = feedparser.parse(feed_url)
            
            # Use clean source name instead of feed title
            source = clean_source_name

            # Process all entries but limit per source
            entries_processed = 0
            for entry in feed.entries:
                if entries_processed >= articles_per_source:
                    break
                    
                # Parse publication date
                pub_date = parse_date(entry.get('published', ''))
                
                # Skip articles older than 48 hours
                if pub_date < cutoff_date:
                    print(f"Skipping old article: {entry.title}")
                    continue
                
                # Check if article should be filtered out
                if should_filter_article(entry.title, entry.get('summary', '')):
                    print(f"Filtered out article: {entry.title}")
                    continue
                
                # Extract and validate image URL with improved methods
                image_url = extract_images_from_entry(entry, feed_url, source)
                
                # Clean and truncate summary
                summary = entry.get('summary', '')
                if summary:
                    # Remove HTML tags for cleaner text
                    soup = BeautifulSoup(summary, 'html.parser')
                    clean_summary = soup.get_text()
                    summary = clean_summary[:300] + '...' if len(clean_summary) > 300 else clean_summary
                else:
                    summary = ''

                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')),
                    'pub_date': pub_date,  # For sorting
                    'summary': summary,
                    'source': source,  # Use clean source name
                    'image_url': image_url
                })
                
                entries_processed += 1
                source_article_count[source] += 1
                time.sleep(0.05)  # Be respectful to servers
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    # Sort articles by publication date (newest first)
    articles.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # Limit to 50 articles total
    articles = articles[:50]
    
    print(f"Total articles fetched: {len(articles)}")
    for source, count in source_article_count.items():
        print(f"  {source}: {count} articles")
    
    return articles

def generate_news_json():
    """Generate a JSON file with the latest news articles"""
    # Fetch articles
    articles = fetch_articles()
    
    # Remove the pub_date field as it's only for sorting
    for article in articles:
        if 'pub_date' in article:
            del article['pub_date']
    
    # Create the data structure
    news_data = {
        'articles': articles,
        'lastUpdated': datetime.now().isoformat(),
        'totalArticles': len(articles)
    }
    
    # Save to JSON file
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"Generated news.json with {len(articles)} articles")
    return news_data

if __name__ == '__main__':
    generate_news_json()