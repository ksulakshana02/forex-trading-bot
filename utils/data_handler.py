import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
import config

class MarketDataHandler:
    def __init__(self):
        if not mt5.initialize():
            print("MT5 initialization failed in DataHandler")

    def get_data(self, symbol, timeframe=config.TIMEFRAME, lookback=1000):
        """
        Fetch data from MT5 and calculate technical indicators.
        """
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, lookback)
        
        if rates is None:
            # Attempt Reconnection
            error_code, error_desc = mt5.last_error()
            print(f"[Data] Failed to fetch {symbol} (Error: {error_code} {error_desc}). Reconnecting...")
            
            mt5.shutdown()
            if not mt5.initialize():
                 print(f"[Data] MT5 Re-init Failed: {mt5.last_error()}")
                 return None
            
            # Retry Once
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, lookback)
            
        if rates is None or len(rates) < lookback:
            print(f"[Data] Generic Failure or insufficient data for {symbol}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # === Feature Engineering ===
        
        # Price Action
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving Averages
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_100'] = ta.ema(df['close'], length=100)
        df['ema_200'] = ta.ema(df['close'], length=200)
        
        # Momentum
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        
        # Volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        # Handle dynamic column names from pandas_ta
        # It typically returns BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        # But depending on version/precision it might vary.
        if bb is not None:
            # Find columns dynamically
            col_lower = [c for c in bb.columns if c.startswith('BBL')][0]
            col_mid = [c for c in bb.columns if c.startswith('BBM')][0]
            col_upper = [c for c in bb.columns if c.startswith('BBU')][0]
            
            df['bb_upper'] = bb[col_upper]
            df['bb_lower'] = bb[col_lower]
            df['bb_mid'] = bb[col_mid]
        
        # Trend Strength
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx['ADX_14']
        
        # Advanced Statistical Features
        # Rolling Z-Score (Mean Reversion)
        df['mean_100'] = df['close'].rolling(100).mean()
        df['std_100'] = df['close'].rolling(100).std()
        df['z_score'] = (df['close'] - df['mean_100']) / df['std_100']
        
        # Volatility Regime
        df['volatility_20'] = df['returns'].rolling(20).std()
        
        return df.dropna()
