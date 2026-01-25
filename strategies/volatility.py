from .base import BaseStrategy
import pandas as pd

class VolatilityRegimeStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Volatility Regime")

    def generate_signal(self, df: pd.DataFrame):
        latest = df.iloc[-1]
        
        # Determine Regime
        # High vol = Mean Reversion failure risk, but Trend opportunity
        # Low vol = Mean Reversion opportunity (range trading)
        
        vol_percentile = df['volatility_20'].rank(pct=True).iloc[-1]
        
        bb_pos = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        
        signal = None
        confidence = 0.0
        
        # Low Volatilty Regime (Range Trading)
        if vol_percentile < 0.30:
            if bb_pos < 0.1: # Near lower band
                signal = "BUY"
                confidence = 0.7
            elif bb_pos > 0.9: # Near upper band
                signal = "SELL"
                confidence = 0.7
                
        # High Volatility Regime (Breakout/Trend continuation)
        elif vol_percentile > 0.70:
            price = latest['close']
            if price > latest['bb_upper'] and latest['rsi'] > 50:
                signal = "BUY" # Breakout Logc
                confidence = 0.6
            elif price < latest['bb_lower'] and latest['rsi'] < 50:
                signal = "SELL"
                confidence = 0.6
                
        return signal, confidence
