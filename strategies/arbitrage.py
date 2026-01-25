from .base import BaseStrategy
import pandas as pd

class StatisticalArbitrageStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Statistical Arbitrage")

    def generate_signal(self, df: pd.DataFrame):
        latest = df.iloc[-1]
        
        # Z-Score Logic
        z_score = latest['z_score']
        rsi = latest['rsi']
        
        signal = None
        confidence = 0.0
        
        # Extreme Oversold (Mean Reversion Long)
        if z_score < -2.5 and rsi < 30:
            signal = "BUY"
            # Confidence scales with extremeness
            confidence = min(abs(z_score) / 4.0, 1.0) 
            
        # Extreme Overbought (Mean Reversion Short)
        elif z_score > 2.5 and rsi > 70:
            signal = "SELL"
            confidence = min(abs(z_score) / 4.0, 1.0)
            
        return signal, confidence
