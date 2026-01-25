from .news_feed import NewsHarvester
from .sentiment_engine import SentimentEngine
from datetime import datetime
import pandas as pd

class NewsHandler:
    def __init__(self):
        print("[News] Initializing News Filter...")
        try:
            self.harvester = NewsHarvester()
            self.brain = SentimentEngine()
            self.active = True
        except Exception as e:
            print(f"[News] Failed to init news system: {e}")
            self.active = False

    def get_market_sentiment(self, symbol="EURUSD"):
        """
        Fetches latest news and returns a sentiment score (-1.0 to 1.0)
        and a 'safe to trade' flag.
        """
        if not self.active:
            return 0.0, True

        try:
            news_df = self.harvester.fetch_latest_news(limit=5)
            if news_df.empty:
                return 0.0, True
            
            # Simple keyword filter for the symbol
            currency = symbol[:3] # EUR
            quote = symbol[3:]    # USD
            
            relevant_headlines = []
            for _, row in news_df.iterrows():
                title = row['title']
                # Check if matches currency pairs or general market keywords
                if any(k in title for k in [currency, quote, "Fed", "ECB", "Market", "Dollar", "Euro", "Yen"]):
                    relevant_headlines.append(title)
            
            if not relevant_headlines:
                return 0.0, True

            # Analyze sentiment of relevant headlines
            sentiment_score = 0.0
            count = 0
            
            for headline in relevant_headlines:
                result = self.brain.analyze(headline)
                if result:
                    score = result['score'] if result['label'] == 'positive' else -result['score']
                    if result['label'] == 'neutral':
                        score = 0
                    
                    sentiment_score += score
                    count += 1
            
            if count == 0:
                return 0.0, True
            
            avg_sentiment = sentiment_score / count
            
            # Impact Filter: If sentiment is EXTREME, maybe risky? 
            # Or use it as bias.
            # Here: We return the bias.
            
            return avg_sentiment, True

        except Exception as e:
            print(f"[News] Error filtering: {e}")
            return 0.0, True
