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

class NewsHarvester:
    def __init__(self):
        # Added Investing.com (Forex) and CoinDesk (Crypto) for better coverage
        self.rss_urls = [
            "https://finance.yahoo.com/news/rssindex",
            "https://www.dailyfx.com/feeds/market-news",
            "https://www.investing.com/rss/news_25.rss",  # Investing.com Forex
            "https://www.coindesk.com/arc/outboundfeeds/rss/" # CoinDesk (Crypto)
        ]
        print("Advanced News Harvester initialized.")

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

                    news_item = {
                        'source': self._get_source_name(url),
                        'title': entry.title,
                        'link': entry.link,
                        'published': datetime.now() # Simplified for speed
                    }
                    all_news.append(news_item)
            except Exception as e:
                pass # Silently ignore connection errors to keep bot running

        if all_news:
            return pd.DataFrame(all_news)
        else:
            return pd.DataFrame()

    def _get_source_name(self, url):
        if "yahoo" in url: return "Yahoo"
        if "dailyfx" in url: return "DailyFX"
        if "investing" in url: return "Investing.com"
        if "coindesk" in url: return "CoinDesk"
        return "Unknown"