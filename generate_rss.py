
import requests
import datetime
import xml.etree.ElementTree as ET
import re
import os
from urllib.parse import quote

def clean_text(text):
    """Clean text for XML compatibility"""
    if not text:
        return 'No description available.'
    # Remove invalid XML characters and HTML tags
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', '', text)
    return text.strip()

def is_recent_article(published_at, hours_limit=24):
    """Check if article is within the specified hours limit"""
    try:
        # Parse the published date
        article_date = datetime.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
        # Get current UTC time
        current_time = datetime.datetime.utcnow()
        # Calculate time difference
        time_diff = current_time - article_date
        return time_diff.total_seconds() / 3600 <= hours_limit
    except:
        return False

def is_quality_source(source_name):
    """Filter for reputable news sources"""
    quality_sources = {
        'Reuters', 'Associated Press', 'BBC News', 'The Guardian', 
        'NPR', 'PBS NewsHour', 'Financial Times', 'The Economist',
        'Nature', 'Science', 'MIT Technology Review', 'IEEE Spectrum',
        'The New York Times', 'The Washington Post', 'Wall Street Journal',
        'CNBC', 'Bloomberg', 'Al Jazeera English'
    }
    return source_name in quality_sources

# Get API key from environment variable
API_KEY = os.getenv('NEWSAPI_KEY', '')
if not API_KEY:
    print("Error: NEWSAPI_KEY environment variable not set")
    exit(1)

# Enhanced search queries for better content quality
SEARCH_QUERIES = {
    'global': [
        'international diplomacy',
        'global economy',
        'climate change policy',
        'international trade',
        'global health WHO'
    ],
    'Europe': [
        'European Union policy',
        'European Parliament',
        'European Central Bank',
        'European Commission',
        'Brexit aftermath'
    ],
    'Asia': [
        'ASEAN summit',
        'Asian economic growth',
        'China policy',
        'Japan technology',
        'India development'
    ],
    'South America': [
        'Latin America economy',
        'Amazon rainforest',
        'South American trade',
        'Brazil politics',
        'Argentina economy'
    ],
    'North America': [
        'US Congress',
        'Canadian policy',
        'NAFTA USMCA',
        'North American trade',
        'Federal Reserve'
    ],
    'Africa': [
        'African Union',
        'African development',
        'Sub-Saharan Africa',
        'African economy',
        'African climate'
    ],
    'Science': [
        'peer-reviewed research',
        'scientific discovery',
        'space exploration NASA',
        'climate science',
        'medical research'
    ],
    'Technology': [
        'artificial intelligence research',
        'quantum computing',
        'cybersecurity policy',
        'technology regulation',
        'innovation breakthrough'
    ],
    'Business': [
        'corporate earnings',
        'economic indicators',
        'central bank policy',
        'market regulation',
        'trade agreements'
    ],
    'Health': [
        'public health policy',
        'medical breakthrough',
        'healthcare system',
        'disease prevention',
        'WHO announcement'
    ],
    'Environment': [
        'climate policy',
        'renewable energy',
        'environmental protection',
        'carbon emissions',
        'sustainability'
    ],
    'Politics': [
        'government policy',
        'election results',
        'political reform',
        'international relations',
        'diplomatic negotiations'
    ],
    'Society': [
        'social policy',
        'education reform',
        'demographic changes',
        'cultural development',
        'social movements'
    ]
}

# Define the regions and topics for each day of the week
weekly_rotation = {
    'Monday': {'region': 'Europe', 'topic': 'Science'},
    'Tuesday': {'region': 'Asia', 'topic': 'Business'},
    'Wednesday': {'region': 'South America', 'topic': 'Technology'},
    'Thursday': {'region': 'North America', 'topic': 'Health'},
    'Friday': {'region': 'Africa', 'topic': 'Environment'},
    'Saturday': {'region': 'Global', 'topic': 'Politics'},
    'Sunday': {'region': 'Local', 'topic': 'Society'}
}

# Get today's day of the week
today = datetime.datetime.now().strftime('%A')
region_focus = weekly_rotation[today]['region']
topic_focus = weekly_rotation[today]['topic']

def fetch_headlines(query_type, query_list, page_size=10):
    """Fetch headlines with improved error handling and filtering"""
    all_articles = []
    
    for query in query_list[:2]:  # Limit to 2 queries per category to avoid rate limits
        try:
            # Calculate date range for recent articles
            from_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'language': 'en',
                'pageSize': page_size,
                'apiKey': API_KEY,
                'from': from_date,
                'sortBy': 'publishedAt'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                # Filter for quality and recent articles
                for article in data['articles']:
                    # Skip if missing essential fields
                    if not all([article.get('title'), article.get('url'), 
                               article.get('publishedAt'), article.get('source', {}).get('name')]):
                        continue
                    
                    # Check if article is recent
                    if not is_recent_article(article['publishedAt']):
                        continue
                    
                    # Check source quality (optional - you may want to relax this)
                    source_name = article.get('source', {}).get('name', '')
                    # Comment out the quality filter if you want more sources
                    # if not is_quality_source(source_name):
                    #     continue
                    
                    # Avoid duplicates
                    if article not in all_articles:
                        all_articles.append(article)
                        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {query}: {e}")
            continue
        except Exception as e:
            print(f"Error processing {query}: {e}")
            continue
    
    # Sort by publication date (newest first) and return top results
    all_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    return all_articles[:page_size]

def format_rss_date(date_string):
    """Convert ISO date to RFC 2822 format for RSS"""
    try:
        dt = datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
        # Convert to UTC and format for RSS
        return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
    except:
        # Fallback to current time if parsing fails
        return datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

def create_rss_feed(global_headlines, regional_headlines, topic_headlines):
    """Create RSS feed with proper XML structure"""
    
    # Create RSS root element
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = ET.SubElement(rss, 'channel')
    
    # Channel metadata
    title = ET.SubElement(channel, 'title')
    title.text = 'Daily Global News Digest'
    
    link = ET.SubElement(channel, 'link')
    link.text = 'https://dshadle1524.github.io'
    
    description = ET.SubElement(channel, 'description')
    description.text = f'Daily curated headlines: Global news, {region_focus} regional focus, {topic_focus} topic focus'
    
    # Current time in RFC 2822 format
    current_time = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    pub_date = ET.SubElement(channel, 'pubDate')
    pub_date.text = current_time
    
    last_build_date = ET.SubElement(channel, 'lastBuildDate')
    last_build_date.text = current_time
    
    # Atom link for RSS feed
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', 'https://dshadle1524.github.io/daily_newsletter.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    def add_articles_to_feed(articles, category=None):
        """Helper function to add articles to RSS feed"""
        for article in articles:
            item = ET.SubElement(channel, 'item')
            
            # Title
            title_elem = ET.SubElement(item, 'title')
            title_elem.text = clean_text(article.get('title', 'No title'))
            
            # Link
            link_elem = ET.SubElement(item, 'link')
            link_elem.text = article.get('url', '')
            
            # Description
            description_elem = ET.SubElement(item, 'description')
            description_elem.text = clean_text(article.get('description', 'No description available.'))
            
            # Publication date
            pub_date_elem = ET.SubElement(item, 'pubDate')
            pub_date_elem.text = format_rss_date(article.get('publishedAt', ''))
            
            # GUID
            guid_elem = ET.SubElement(item, 'guid')
            guid_elem.text = article.get('url', '')
            
            # Category
            if category:
                category_elem = ET.SubElement(item, 'category')
                category_elem.text = category
            
            # Source
            source_elem = ET.SubElement(item, 'source')
            source_elem.text = article.get('source', {}).get('name', 'Unknown')
    
    # Add articles to feed
    add_articles_to_feed(global_headlines, 'Global')
    add_articles_to_feed(regional_headlines, region_focus)
    add_articles_to_feed(topic_headlines, topic_focus)
    
    # Write XML file with proper formatting
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)  # Pretty print
    tree.write('daily_newsletter.xml', encoding='utf-8', xml_declaration=True)

def main():
    """Main execution function"""
    print(f"Generating RSS feed for {today}")
    print(f"Regional focus: {region_focus}")
    print(f"Topic focus: {topic_focus}")
    
    # Fetch headlines
    print("Fetching global headlines...")
    global_headlines = fetch_headlines('global', SEARCH_QUERIES.get('global', ['global']), 10)
    
    print(f"Fetching {region_focus} regional headlines...")
    regional_headlines = fetch_headlines('regional', SEARCH_QUERIES.get(region_focus, [region_focus.lower()]), 5)
    
    print(f"Fetching {topic_focus} topic headlines...")
    topic_headlines = fetch_headlines('topic', SEARCH_QUERIES.get(topic_focus, [topic_focus.lower()]), 5)
    
    # Create RSS feed
    create_rss_feed(global_headlines, regional_headlines, topic_headlines)
    
    print(f"RSS feed generated successfully with {len(global_headlines)} global, {len(regional_headlines)} regional, and {len(topic_headlines)} topic headlines.")

if __name__ == "__main__":
    main()
