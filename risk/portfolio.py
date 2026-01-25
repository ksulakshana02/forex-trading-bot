import config

class PortfolioManager:
    def __init__(self):
        self.weights = config.STRATEGY_WEIGHTS
        self.active_strategies = list(self.weights.keys())
        
    def get_strategy_weight(self, strategy_name):
        return self.weights.get(strategy_name, 0.0)
    
    def check_correlation(self, new_symbol, active_trades):
        """
        Check if new trade is highly correlated with existing positions.
        Simple logic: Don't trade same pair in same direction multiple times 
        unless strategies differ significantly?
        
        For now: Return True (allow) as a placeholder for complex correlation matrix.
        """
        return True
