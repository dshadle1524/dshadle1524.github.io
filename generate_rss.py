
import requests
import datetime
import xml.etree.ElementTree as ET

import re

def clean_text(text):
    if not text:
        return 'No description available.'
    return re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', '', text)


# Replace 'YOUR_NEWSAPI_KEY' with your actual NewsAPI.org API key
API_KEY = '44f4564d776049e6972376e8a9cf376d'

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

# Get the region and topic for today
region_focus = weekly_rotation[today]['region']
topic_focus = weekly_rotation[today]['topic']

# Function to fetch headlines from NewsAPI
def fetch_headlines(query, language='en', page_size=10):
    url = f'https://newsapi.org/v2/everything?q={query}&language={language}&pageSize={page_size}&apiKey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data['articles']

# Fetch global headlines
global_headlines = fetch_headlines('global', page_size=10)

# Fetch regional headlines
regional_headlines = fetch_headlines(region_focus, page_size=5)

# Fetch topic headlines
topic_headlines = fetch_headlines(topic_focus, page_size=5)

# Function to create an RSS feed
def create_rss_feed(global_headlines, regional_headlines, topic_headlines):
    rss = ET.Element('rss', {'version': '2.0','xmlns:atom': 'http://www.w3.org/2005/Atom'})
    channel = ET.SubElement(rss, 'channel')
    title = ET.SubElement(channel, 'title')
    title.text = 'Daily Newsletter'
    link = ET.SubElement(channel, 'link')
    link.text = 'http://davidshadle.com'
    description = ET.SubElement(channel, 'description')
    description.text = 'Daily curated headlines from around the world.'
    pubDate = ET.SubElement(channel, 'pubDate')
    pubDate.text = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    lastBuildDate = ET.SubElement(channel, 'lastBuildDate')
    lastBuildDate.text = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    atom_link = ET.SubElement(channel, 'atom:link', href='http://davidshadle.com/daily_newsletter.xml', rel='self', type='application/rss+xml')

    # Add global headlines
    for article in global_headlines:
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = article['title']
        link = ET.SubElement(item, 'link')
        link.text = article['url']
        description = ET.SubElement(item, 'description')
        description.text = article['description']
        pubDate = ET.SubElement(item, 'pubDate')
        pubDate.text = datetime.datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%a, %d %b %Y %H:%M:%S %z')
        guid = ET.SubElement(item, 'guid')
        guid.text = article['url']

    # Add regional headlines
    for article in regional_headlines:
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = article['title']
        link = ET.SubElement(item, 'link')
        link.text = article['url']
        description = ET.SubElement(item, 'description')
        description.text = article['description']
        pubDate = ET.SubElement(item, 'pubDate')
        pubDate.text = datetime.datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%a, %d %b %Y %H:%M:%S %z')
        guid = ET.SubElement(item, 'guid')
        guid.text = article['url']
        category = ET.SubElement(item, 'category')
        category.text = region_focus

    # Add topic headlines
    for article in topic_headlines:
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = article['title']
        link = ET.SubElement(item, 'link')
        link.text = article['url']
        description = ET.SubElement(item, 'description')
        description.text = article['description']
        pubDate = ET.SubElement(item, 'pubDate')
        pubDate.text = datetime.datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%a, %d %b %Y %H:%M:%S %z')
        guid = ET.SubElement(item, 'guid')
        guid.text = article['url']
        category = ET.SubElement(item, 'category')
        category.text = topic_focus

    tree = ET.ElementTree(rss)
    tree.write('daily_newsletter.xml', encoding='utf-8', xml_declaration=True)

# Create the RSS feed
create_rss_feed(global_headlines, regional_headlines, topic_headlines)

print("RSS feed generated successfully.")
