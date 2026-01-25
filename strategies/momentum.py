from .base import BaseStrategy
import pandas as pd

class MomentumBreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Momentum Breakout")

    def generate_signal(self, df: pd.DataFrame):
        latest = df.iloc[-1]
        
        # Trend Consensus
        ema_bullish = latest['ema_20'] > latest['ema_50'] > latest['ema_200']
        ema_bearish = latest['ema_20'] < latest['ema_50'] < latest['ema_200']
        
        # Trend Strength
        strong_trend = latest['adx'] > 25
        
        # MACD Confirmation
        macd_bullish = latest['macd'] > latest['macd_signal'] and latest['macd'] > 0
        macd_bearish = latest['macd'] < latest['macd_signal'] and latest['macd'] < 0
        
        signal = None
        confidence = 0.0
        
        if ema_bullish and strong_trend and macd_bullish:
            signal = "BUY"
            # Confidence increases with ADX strength
            confidence = min(latest['adx'] / 60.0, 1.0)
            
        elif ema_bearish and strong_trend and macd_bearish:
            signal = "SELL"
            confidence = min(latest['adx'] / 60.0, 1.0)
            
        return signal, confidence
