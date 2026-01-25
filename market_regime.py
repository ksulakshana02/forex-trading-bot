import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

class MarketRegime:
    def __init__(self):
        # We watch these pairs to confirm USD strength/weakness
        self.correlations = {
            "USDJPY": "Direct",   # If USD is strong, this goes UP
            "XAUUSD": "Inverse",  # If USD is strong, Gold usually goes DOWN
        }
        print("[System] Market Regime 'Judge' Initialized.")


    def get_market_state(self, symbol):
        """
        Returns 'TRENDING' or 'RANGING' using ADX (Average Directional Index).
        """
        # Get 50 candles of H1 data to calculate trend strength
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        
        if rates is None or len(rates) < 50:
            return "UNKNOWN"
        
        df = pd.DataFrame(rates)
        # Calculate ADX with length 14
        try:
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            if adx_df is None or adx_df.empty:
                return "UNKNOWN"
                
            current_adx = adx_df['ADX_14'].iloc[-1]
            
            # ADX > 25 usually indicates a strong trend. 
            # ADX < 20 indicates a sleeping/choppy market.
            if current_adx > 25:
                return "TRENDING"
            else:
                return "RANGING"
        except Exception as e:
            print(f"   ⚠️ Error calculating ADX: {e}")
            return "UNKNOWN"


    def get_trend(self, symbol):
        """Returns 'UP', 'DOWN', or 'FLAT' based on simple Price vs Open"""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return "UNKNOWN"
        
        # Simple Logic: Is current price above the daily open?
        # (For a real system, we'd use moving averages here too)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1)
        if rates is None: return "UNKNOWN"
        
        daily_open = rates[0]['open']
        current_price = tick.bid

        change = (current_price - daily_open) / daily_open
        
        if change > 0.001: return "UP"
        if change < -0.001: return "DOWN"
        return "FLAT"


    def validate_signal(self, proposed_pair, signal_type):
        """
        Validates EURUSD trade against USDJPY.
        """
        if "USD" not in proposed_pair: return True 

        print(f"   [Judge] Validating {signal_type} signal on {proposed_pair}...")

        jpy_trend = self.get_trend("USDJPY")
        
        if signal_type == "BUY":
            # Buy EURUSD = Weak Dollar = USDJPY should be DOWN or FLAT
            if jpy_trend == "UP":
                print(f"   ❌ REJECTED: USDJPY is Rising (Dollar Strong). Unsafe to Buy EUR.")
                return False
        
        elif signal_type == "SELL":
            # Sell EURUSD = Strong Dollar = USDJPY should be UP or FLAT
            if jpy_trend == "DOWN":
                print(f"   ❌ REJECTED: USDJPY is Falling (Dollar Weak). Unsafe to Sell EUR.")
                return False

        print(f"   ✅ CONFIRMED: Regime supports trade (USDJPY is {jpy_trend}).")
        return True