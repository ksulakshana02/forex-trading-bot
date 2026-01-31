# import feedparser
# import pandas as pd
# from datetime import datetime
# import time

# class NewsHarvester:
#     def __init__(self):
#         # We will use Yahoo Finance and DailyFX RSS feeds (Free & Public)
#         self.rss_urls = [
#             "https://finance.yahoo.com/news/rssindex",
#             "https://www.dailyfx.com/feeds/market-news"
#         ]
#         print("News Harvester initialized.")

#     def fetch_latest_news(self, limit=5):
#         """
#         Fetches the latest unique headlines from all sources.
#         """
#         all_news = []
        
#         print(f"Checking for news at {datetime.now().strftime('%H:%M:%S')}...")
        
#         for url in self.rss_urls:
#             try:
#                 feed = feedparser.parse(url)
#                 # Loop through entries in the feed
#                 for entry in feed.entries[:limit]:
#                     news_item = {
#                         'source': 'Yahoo' if 'yahoo' in url else 'DailyFX',
#                         'title': entry.title,
#                         'link': entry.link,
#                         'published': entry.get('published', datetime.now())
#                     }
#                     all_news.append(news_item)
#             except Exception as e:
#                 print(f"Error fetching {url}: {e}")

#         # Convert to DataFrame for easier handling
#         if all_news:
#             df = pd.DataFrame(all_news)
#             return df
#         else:
#             return pd.DataFrame()

# # --- Unit Test Area ---
# if __name__ == "__main__":
#     harvester = NewsHarvester()
    
#     # Fetch news
#     news_df = harvester.fetch_latest_news(limit=3)
    
#     if not news_df.empty:
#         print("\n--- Latest Live News ---")
#         for index, row in news_df.iterrows():
#             print(f"[{row['source']}] {row['title']}")
#     else:
#         print("No news found. Check internet connection.")


import feedparser
import pandas as pd
from datetime import datetime
import time
import cloudscraper
from bs4 import BeautifulSoup

class NewsHarvester:
    def __init__(self):
        # Added Investing.com (Forex) and CoinDesk (Crypto) for better coverage
        self.rss_urls = [
            "https://finance.yahoo.com/news/rssindex",
            "https://www.dailyfx.com/feeds/market-news",
            "https://www.investing.com/rss/news_25.rss",  # Investing.com Forex
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://www.forexlive.com/feed/news",        # PRO SOURCE: Extremely fast sentiment
            "https://www.fxstreet.com/rss/news"           # PRO SOURCE: Good coverage
        ]
        self.scraper = cloudscraper.create_scraper() # create a Cloudflare-bypassing scraper
        print("Advanced News Harvester (Cloudscraper) initialized.")

    def fetch_latest_news(self, limit=5):
        all_news = []
        seen_titles = set() # To remove duplicates
        
        # print(f"Checking {len(self.rss_urls)} news sources...")
        
        for url in self.rss_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:limit]:
                    
                    # Deduplication check
                    if entry.title in seen_titles:
                        continue
                    seen_titles.add(entry.title)
                    
                    # Try to get summary/description
                    summary = ""
                    if hasattr(entry, 'summary'):
                         summary = entry.summary
                    elif hasattr(entry, 'description'):
                         summary = entry.description

                    news_item = {
                        'source': self._get_source_name(url),
                        'title': entry.title,
                        'link': entry.link,
                        'published': datetime.now(), # Simplified for speed
                        'summary': summary
                    }
                    all_news.append(news_item)
            except Exception as e:
                pass # Silently ignore connection errors to keep bot running

        if all_news:
            return pd.DataFrame(all_news)
        else:
            return pd.DataFrame()

    def fetch_article_content(self, url):
        """
        Scrapes the main text content from a news URL.
        """
        try:
            # Custom headers for difficult sites
            headers = {}
            if "wsj.com" in url or "bloomberg.com" in url or "reuters.com" in url or "investing.com" in url:
                # Mimic Googlebot to bypass some soft paywalls and anti-bot checks
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Referer": "https://www.google.com/"
                }
                # Use standard requests for this hack, as cloudscraper might override UA
                import requests
                response = requests.get(url, headers=headers, timeout=10)
            else:
                # Use cloudscraper for standard sites (bypasses Cloudflare)
                response = self.scraper.get(url, timeout=10)
            
            if response.status_code != 200:
                # Silently fail for 401/403 to avoid console spam for paywalls
                if response.status_code not in [401, 403]:
                    print(f"[Scraper] Failed to fetch {url} (Status: {response.status_code})")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Heuristic to find main content (works for many finance sites)
            # 1. Try common article tags
            paragraphs = []
            
            # Specific site logic
            if "wsj.com" in url:
                paragraphs = soup.find_all('p') # WSJ often puts content in P tags directly under main
            else:
                article_body = soup.find('article') or soup.find('div', class_='article-content') or soup.find('div', class_='content') or soup.find('div', class_='articleBody')
                
                if article_body:
                    paragraphs = article_body.find_all('p')
                else:
                    # Fallback: just all paragraphs
                    paragraphs = soup.find_all('p')
                
            text = " ".join([p.get_text() for p in paragraphs])
            
            # Clean up
            text = " ".join(text.split()) # Remove excess whitespace
            
            if len(text) < 200: # Too short, probably failed or just a preview
                return None
                
            return text
            
        except Exception as e:
            # print(f"[Scraper] Error scraping {url}: {e}") # Suppress generic errors
            return None

    def _get_source_name(self, url):
        if "yahoo" in url: return "Yahoo"
        if "dailyfx" in url: return "DailyFX"
        if "investing" in url: return "Investing.com"
        if "coindesk" in url: return "CoinDesk"
        if "forexlive" in url: return "ForexLive"
        if "fxstreet" in url: return "FXStreet"
        return "Unknown"