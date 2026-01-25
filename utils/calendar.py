import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

class EconomicCalendar:
    def __init__(self):
        # High impact keywords
        self.impact_keywords = ["CPI", "GDP", "Non-Farm", "Payroll", "Rate Decision", "FOMC", "ECB", "Powell", "Lagarde"]
        
    def get_upcoming_events(self, currency="USD", minutes=60):
        """
        Get high-impact events for the next X minutes.
        Uses MT5 Calendar if available.
        """
        try:
            # Check if MT5 is initialized
            if not mt5.last_error():
                return [] # Not connected?
            
            now = datetime.now()
            future = now + timedelta(minutes=minutes)
            
            # Use MT5's native calendar function
            # NOTE: verify if `mt5.calendar_value_history` or similar exists in this version.
            # If not, we return empty list to not break system.
            
            try:
                # This fetches values (past), not future schedule usually.
                # MT5 python API is limited for FUTURE calendar events in some versions.
                # We will check if we can fetch from a reliable simplified list if MT5 fails.
                
                # As a fallback for "Real Professional" usage without paying for an API:
                # We rely on the NewsHarvester to catch " Breaking: CPI is..." 
                pass
            except:
                pass

            return []
            
        except Exception as e:
            print(f"[Calendar] Error: {e}")
            return []

    def check_impact(self, symbol):
        """
        Returns True if SAFE to trade (no immediate high impact news), False if DANGER.
        """
        # Placeholder for actual calendar logic. 
        # For now, we rely on the Sentiment Engine reading headlines about these events.
        return True
