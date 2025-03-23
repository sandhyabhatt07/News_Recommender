import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from newspaper import Article
import re

# ✅ Define clean_text() to avoid NameError
def clean_text(text):
    """Removes special characters and converts text to lowercase."""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    return text.lower().strip()  # Convert to lowercase and trim spaces

# Function to remove HTML tags from text
def remove_html_tags(text):
    """Removes HTML tags from the given text."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

# Define Google News RSS Feeds
RSS_FEEDS = {
   "Top Stories": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "World": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0JtVnpMVFF4T1NnQVAB?hl=en-US&gl=US&ceid=US:en",
    "Technology": "https://news.google.com/rss/search?q=technology&hl=en-US&gl=US&ceid=US:en",
    "Sports": "https://news.google.com/rss/search?q=sports&hl=en-US&gl=US&ceid=US:en",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Entertainment": "https://news.google.com/rss/search?q=entertainment&hl=en-US&gl=US&ceid=US:en",
    "Lifestyle": "https://news.google.com/rss/search?q=lifestyle&hl=en-US&gl=US&ceid=US:en",
    "Weather": "https://news.google.com/rss/search?q=weather&hl=en-US&gl=US&ceid=US:en",
    "Shopping": "https://news.google.com/rss/search?q=shopping&hl=en-US&gl=US&ceid=US:en",
    "Travel": "https://news.google.com/rss/search?q=travel&hl=en-US&gl=US&ceid=US:en",
    "Wealth": "https://news.google.com/rss/search?q=wealth&hl=en-US&gl=US&ceid=US:en"
}

# Function to extract full article text
def extract_full_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text if article.text else "Full article unavailable."
    except Exception as e:
        print(f"⚠️ Error extracting article from {url}: {e}")
        return "Full article unavailable."

# Function to extract image from metadata
def extract_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        image_tag = soup.find("meta", property="og:image")
        return image_tag["content"] if image_tag else "https://via.placeholder.com/150"
    except Exception as e:
        print(f"⚠️ Error extracting image from {url}: {e}")
        return "https://via.placeholder.com/150"

# Function to fetch news articles
def fetch_news(feed_url):
    print(f"🔍 Fetching news from: {feed_url}")  # Debugging print

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    response = requests.get(feed_url, headers=headers)

    if response.status_code != 200:
        print(f"⚠️ Failed to fetch RSS feed. HTTP Status: {response.status_code}")
        return []

    news_feed = feedparser.parse(response.content)

    if not news_feed.entries:
        print(f"⚠️ No articles found for {feed_url}.")
        return []

    articles = []
    for entry in news_feed.entries[:10]:  # Limit to 10 articles per category
        title = entry.title
        link = entry.link
        summary = extract_full_article(link)  # Try to extract the full article
        if summary == "Full article unavailable.":
            summary = entry.summary  # Fallback to the summary from RSS feed
        published = entry.get("published", "No date available")
        image_url = extract_image(link)

        # Remove HTML tags from the summary text
        cleaned_summary = remove_html_tags(summary)

        print(f"📰 {title}")  # Debugging print: show each fetched article

        articles.append({
            "title": title,
            "link": link,
            "summary": summary,
            "cleaned_summary": cleaned_summary,
            "published": published,
            "image": image_url
        })

    return articles

# Function to get news and return as DataFrame
def get_news_dataframe():
    all_articles = []
    for category, url in RSS_FEEDS.items():
        articles = fetch_news(url)
        for article in articles:
            article["category"] = category
            all_articles.append(article)

    df = pd.DataFrame(all_articles)

    if df.empty:
        print("⚠️ Error: No articles were fetched. Check your RSS feeds or internet connection.")
    else:
        print(f"✅ Successfully fetched {len(df)} articles.")

    return df

# Main execution
if __name__ == "__main__":
    news_df = get_news_dataframe()
    
    if not news_df.empty:
        print(news_df.head())  # Print first few rows
