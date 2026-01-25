import MetaTrader5 as mt5
import numpy as np
import config

class RiskManager:
    def __init__(self, database):
        self.db = database
        self.daily_risk_used = 0.0
        
    def check_daily_limits(self, potential_risk):
        """Check if trade exceeds max daily risk"""
        # Fetch available equity
        account = mt5.account_info()
        if not account:
            return False
            
        if self.daily_risk_used + potential_risk > config.MAX_DAILY_RISK:
            print(f"[Risk] Daily risk limit reached ({self.daily_risk_used:.2%})")
            return False
            
        return True

    def calculate_position_size(self, symbol, sl_distance, confidence, win_rate=0.55):
        """
        Calculate position size using Half-Kelly Criterion.
        
        Kelly % = (p(b+1) - 1) / b
        where:
        p = probability of win (win_rate)
        b = odds received (reward_to_risk ratio)
        """
        account = mt5.account_info()
        if not account:
            return 0.0
        
        balance = account.balance
        
        # Reward to Risk (approximate target)
        reward_risk_ratio = 2.0  # Conservative estimate, or dynamic based on TP/SL
        
        # Kelly Formula
        # K = W - (1-W)/R
        kelly_fraction = win_rate - (1 - win_rate) / reward_risk_ratio
        
        # Use Half-Kelly for safety
        kelly_fraction *= 0.5
        
        # Cap at max risk per trade (e.g., 2% absolute max even if Kelly says 10%)
        # And scale by confidence
        base_risk_pct = min(kelly_fraction, config.BASE_RISK_PER_TRADE * 2)
        risk_pct = base_risk_pct * confidence
        
        # Ensure non-negative
        risk_pct = max(0.0, risk_pct)
        risk_amount = balance * risk_pct
        
        # Calculate Lots
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.0
            
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        
        if tick_value == 0 or tick_size == 0:
            return 0.01 # Fallback min lot
            
        # Risk Amount = Lots * (SL_Distance / Tick_Size) * Tick_Value
        # Lots = Risk_Amount / (...)
        
        lots = risk_amount / ((sl_distance / tick_size) * tick_value)
        
        # Normalize to lot steps
        step = symbol_info.volume_step
        lots = round(lots / step) * step
        
        lots = max(symbol_info.volume_min, min(lots, symbol_info.volume_max))
        
        return lots

    def update_daily_risk(self, risk_amount_pct):
        self.daily_risk_used += risk_amount_pct
        
    def reset_daily_risk(self):
        self.daily_risk_used = 0.0
