import pandas as pd
from .base import BaseStrategy

class FundamentalStrategy(BaseStrategy):
    def __init__(self, news_handler):
        super().__init__("Fundamental Analysis")
        self.news_handler = news_handler

    def generate_signal(self, df: pd.DataFrame, symbol: str = ""):
        """
        Generates a signal based on news sentiment/LLM analysis.
        """
        if not symbol:
            return None, 0.0

        sentiment, safe = self.news_handler.get_market_sentiment(symbol)
        
        # Range -1.0 to 1.0 (approx)
        # If > 0.4 -> BUY
        # If < -0.4 -> SELL
        
        if sentiment > 0.4:
            # Scale sentiment to confidence 0.0-1.0
            # 0.4 -> ~0.5, 0.8 -> 0.9
            confidence = min(abs(sentiment) + 0.2, 1.0)
            return "BUY", confidence
        elif sentiment < -0.4:
             confidence = min(abs(sentiment) + 0.2, 1.0)
             return "SELL", confidence
             
        return None, 0.0

    def generate_signal_with_symbol(self, df: pd.DataFrame, symbol: str):
         # New method to support symbol
        sentiment, safe = self.news_handler.get_market_sentiment(symbol)
        
        # Range -1.0 to 1.0
        # If > 0.5 -> BUY
        # If < -0.5 -> SELL
        
        if sentiment > 0.5:
            # Scale confidence: 0.5 -> 0.5, 1.0 -> 1.0
            confidence = sentiment
            return "BUY", confidence
        elif sentiment < -0.5:
             confidence = abs(sentiment)
             return "SELL", confidence
             
        return None, 0.0
