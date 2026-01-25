from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame):
        """
        Analyze the provided DataFrame and return a signal.
        
        Args:
            df (pd.DataFrame): Market data with indicators.
            
        Returns:
            tuple: (signal, confidence)
                signal (str): "BUY", "SELL", or None
                confidence (float): 0.0 to 1.0
        """
        pass
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optional: Strategy-specific indicator calculation.
        Can be overridden if the strategy needs specific indicators 
        not provided by the main data handler.
        """
        return df
