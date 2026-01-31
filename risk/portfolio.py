import config

class PortfolioManager:
    def __init__(self):
        self.weights = config.STRATEGY_WEIGHTS.copy() # Make a mutable copy
        self.active_strategies = list(self.weights.keys())
        
    def get_strategy_weight(self, strategy_name):
        return self.weights.get(strategy_name, 0.0)

    def optimize_weights(self, db_handler):
        """
        Adjust weights based on realized performance (Win Rate).
        """
        print("[Portfolio] Optimizing strategy weights based on performance...")
        
        # Get win rates (last 50 trades)
        win_rates = db_handler.get_strategy_performance(lookback=50)
        
        if not win_rates:
            print("[Portfolio] Not enough data to optimize. Keeping default weights.")
            return

        new_weights = {}
        total_score = 0.0
        
        for name in self.weights.keys():
            base_weight = config.STRATEGY_WEIGHTS.get(name, 0.2)
            
            # If we have data, use it. Else use default expectation (0.5)
            win_rate = win_rates.get(name, 0.5)
            
            # Algorithm: 
            # Multiplier = 0.5 + Win_Rate
            # If WR is 60%, Mult = 1.1. If 40%, Mult = 0.9.
            # We cap the multiplier to avoid extreme swings (e.g. 0.5 to 1.5 range)
            multiplier = 0.5 + win_rate
            
            score = base_weight * multiplier
            new_weights[name] = score
            total_score += score
            
            print(f"   > {name}: Win Rate {win_rate:.0%} -> Score {score:.3f}")
            
        # Normalize to sum to 1.0 (or slightly more/less depending on conviction?)
        # Let's normalize to 1.0 to keep total risk consistent
        if total_score > 0:
            for name in new_weights:
                self.weights[name] = new_weights[name] / total_score
                
        print("[Portfolio] New Weights Distribution:")
        for name, w in self.weights.items():
            print(f"   - {name}: {w:.1%}")
    
    def check_correlation(self, new_symbol, new_direction, active_positions, data_handler):
        """
        Check if new trade is highly correlated with existing positions.
        Returns: True (Allowed) or False (Blocked)
        """
        if not active_positions:
            return True
            
        print(f"[Risk] Checking correlation for {new_symbol} ({new_direction})...")
        
        # Get data for new symbol
        df_new = data_handler.get_data(new_symbol, lookback=100)
        if df_new is None or df_new.empty:
            print(f"  [Risk] No data for {new_symbol}, skipping correlation check (Allowing).")
            return True
            
        for pos in active_positions:
            active_symbol = pos.symbol
            active_direction = "BUY" if pos.type == 0 else "SELL" # 0=Buy, 1=Sell in MT5
            
            # Skip self (shouldn't happen if logical checks are correct upstream)
            if active_symbol == new_symbol:
                continue
                
            # Get data for active symbol
            df_active = data_handler.get_data(active_symbol, lookback=100)
            if df_active is None or df_active.empty:
                continue
                
            # Align dataframes by index (time) to ensure we compare same candles
            # Use inner join to only keep overlapping times
            common_index = df_new.index.intersection(df_active.index)
            
            if len(common_index) < 50:
                 # Not enough overlapping data
                 continue
                 
            s1 = df_new.loc[common_index]['close']
            s2 = df_active.loc[common_index]['close']
            
            # Calculate Correlation
            correlation = s1.corr(s2)
            
            # Logic:
            # 1. High Positive Correlation (> 0.70)
            #    - If Directions are SAME -> High Risk (Doubling down) -> BLOCK
            #    - If Directions are OPPOSITE -> Hedge -> ALLOW
            
            # 2. High Negative Correlation (< -0.70)
            #    - If Directions are OPPOSITE -> High Risk (Doubling down) -> BLOCK
            #    - If Directions are SAME -> Hedge -> ALLOW
            
            if correlation > config.MAX_CORRELATION and new_direction == active_direction:
                print(f"  [Risk] BLOCKED: {new_symbol} vs {active_symbol} Corr: {correlation:.2f} (Same Direction)")
                return False
                
            elif correlation < -config.MAX_CORRELATION and new_direction != active_direction:
                print(f"  [Risk] BLOCKED: {new_symbol} vs {active_symbol} Corr: {correlation:.2f} (Inv Direction)")
                return False
                
        return True
