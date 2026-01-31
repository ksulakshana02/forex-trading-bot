from .news_feed import NewsHarvester
from .sentiment_engine import SentimentEngine
from .llm_analyzer import LLMMarketAnalyzer
from datetime import datetime
import pandas as pd

class NewsHandler:
    def __init__(self):
        print("[News] Initializing News Filter...")
        try:
            self.harvester = NewsHarvester()
            self.brain = SentimentEngine()
            self.llm_brain = LLMMarketAnalyzer()
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

            # === LLM ENHANCEMENT ===
            # If we have the LLM, let's try to get a deeper signal from the most relevant news
            if self.llm_brain.llm:
                # Take the most recent relevant headline and fetch content
                latest_relevant = news_df[news_df['title'].isin(relevant_headlines)].iloc[0]
                article_url = latest_relevant['link']
                
                print(f"[News] Deep analyzing: {latest_relevant['title']}")
                article_content = self.harvester.fetch_article_content(article_url)
                
                # FALLBACK: Use RSS summary if scraping failed or returned empty
                if not article_content and 'summary' in latest_relevant and len(latest_relevant['summary']) > 50:
                    print(f"  [Scraper] Using RSS summary fallback (Length: {len(latest_relevant['summary'])})")
                    article_content = latest_relevant['summary']
                
                if article_content:
                    llm_result = self.llm_brain.analyze_article(article_content)
                    if llm_result:
                        print(f"  [LLM] Signal: {llm_result['decision']} ({llm_result['confidence']:.2f})")
                        print(f"  [LLM] Reason: {llm_result['reasoning']}")
                        
                        # Override sentiment score
                        if llm_result['decision'] == 'BUY':
                            return float(llm_result['confidence']), True
                        elif llm_result['decision'] == 'SELL':
                            return -float(llm_result['confidence']), True
                        else:
                            return 0.0, True
            
            # === FALLBACK TO HL SENTIMENT ===
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
