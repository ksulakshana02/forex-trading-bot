import MetaTrader5 as mt5
import time
from datetime import datetime
import pandas as pd

import config
from database import DatabaseHandler
from utils.data_handler import MarketDataHandler
from utils.executor import TradeExecutor
from utils.news_handler import NewsHandler
from risk.risk_manager import RiskManager
from risk.portfolio import PortfolioManager

# Strategy Imports
from strategies.arbitrage import StatisticalArbitrageStrategy
from strategies.momentum import MomentumBreakoutStrategy
from strategies.volatility import VolatilityRegimeStrategy
from strategies.ml_ensemble import MLEnsembleStrategy

class TradingBot:
    def __init__(self):
        print("=== INITIALIZING PROFESSIONAL FOREX BOT ===")
        
        # 1. Initialize MT5
        if not mt5.initialize():
            raise Exception(f"MT5 Init Failed: {mt5.last_error()}")
        
        # 2. Components
        self.db = DatabaseHandler()
        self.data_handler = MarketDataHandler()
        self.news_handler = NewsHandler()
        self.executor = TradeExecutor()
        self.risk_manager = RiskManager(self.db)
        self.portfolio = PortfolioManager()
        
        # 3. Strategies
        self.strategies = {
            'statistical_arbitrage': StatisticalArbitrageStrategy(),
            'momentum_breakout': MomentumBreakoutStrategy(),
            'volatility_regime': VolatilityRegimeStrategy(),
            'ml_ensemble': MLEnsembleStrategy()
        }
        
        print(f"[Bot] Initialized with {len(config.SYMBOLS)} pairs and {len(self.strategies)} strategies.")

    def aggregate_signals(self, symbol, df):
        """
        Run all strategies and aggregate votes.
        """
        votes = {'BUY': 0.0, 'SELL': 0.0}
        
        print(f"\n--- Analyzing {symbol} ---")
        
        for name, strategy in self.strategies.items():
            weight = self.portfolio.get_strategy_weight(name)
            signal, confidence = strategy.generate_signal(df)
            
            if signal:
                print(f"  > {name}: {signal} (Conf: {confidence:.2f}, Weight: {weight})")
                votes[signal] += confidence * weight
                
                # Log signal to DB (optional optimization)
            else:
                pass
                # print(f"  > {name}: No Signal")
        
        return votes

    def run_cycle(self):
        """Single trading cycle"""
        current_time = datetime.now()
        
        # Daily Reset
        if current_time.hour == 0 and current_time.minute < 5:
            self.risk_manager.reset_daily_risk()
        
        for symbol in config.SYMBOLS:
            # 1. Get Data
            df = self.data_handler.get_data(symbol)
            if df is None:
                continue

            # 1.5 News Filter
            sentiment, safe_to_trade = self.news_handler.get_market_sentiment(symbol)
            if not safe_to_trade:
                print(f"  [News] High impact news detected for {symbol}. Skipped.")
                continue
            
            if abs(sentiment) > 0.5:
                print(f"  [News] Sentiment Bias: {sentiment:.2f}")

            # 2. Train ML (If model is missing or periodically)
            # Train if no model exists OR every hour at minute 0
            is_new_hour = (current_time.minute == 0)
            model_missing = (self.strategies['ml_ensemble'].model is None)
            
            if model_missing or is_new_hour:
                 print(f"  [ML] Training Model for {symbol}...")
                 self.strategies['ml_ensemble'].train_model(df)
                 # Reload strategy to ensure model is active
                 # (In a real system, we might need to handle this more gracefully)
            
            # 3. Aggregate Signals
            votes = self.aggregate_signals(symbol, df)
            
            # 4. Decision Logic
            winner = None
            max_score = 0.0
            
            if votes['BUY'] > votes['SELL']:
                winner = 'BUY'
                max_score = votes['BUY']
            elif votes['SELL'] > votes['BUY']:
                winner = 'SELL'
                max_score = votes['SELL']
            
            # Threshold (e.g. 0.40 out of 1.0 total weight)
            if winner and max_score > 0.40:
                print(f"  >>> CONSENSUS: {winner} with Score {max_score:.2f}")
                
                # 5. Risk Check
                latest = df.iloc[-1]
                vol_mult = 1.5
                sl_distance = latest['atr'] * vol_mult
                tp_distance = sl_distance * 2.0
                
                # Calculate Lots
                lots = self.risk_manager.calculate_position_size(
                    symbol, sl_distance, confidence=max_score
                )
                
                if lots > 0:
                     # 5.5 Check Sentiment Bias
                    # If sentiment is strongly negative, don't BUY
                    if winner == "BUY" and sentiment < -0.3:
                        print(f"  [News] Trade blocked: Positive signal but Negative Sentiment ({sentiment:.2f})")
                        continue
                    elif winner == "SELL" and sentiment > 0.3:
                        print(f"  [News] Trade blocked: Negative signal but Positive Sentiment ({sentiment:.2f})")
                        continue

                     # 6. Execute
                    result = self.executor.execute_trade(
                        symbol, winner, lots, 
                        price=0, # Market execution handled in executor
                        sl=latest['close'] - sl_distance if winner == 'BUY' else latest['close'] + sl_distance,
                        tp=latest['close'] + tp_distance if winner == 'BUY' else latest['close'] - tp_distance,
                        strategy_name="Ensemble",
                        confidence=max_score
                    )
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        # 7. Log Trade
                        trade_record = {
                            'ticket': result.deal, # Note: result.order provided, ensure deal info fetched if needed
                            'symbol': symbol,
                            'strategy': 'Ensemble',
                            'direction': winner,
                            'entry_time': datetime.now(),
                            'entry_price': result.price,
                            'sl': 0.0, # logged from request if available
                            'tp': 0.0,
                            'volume': lots,
                            'confidence': max_score,
                            'regime': 'Dynamic',
                            'status': 'OPEN',
                            'metrics': {
                                'z_score': latest.get('z_score', 0),
                                'rsi': latest.get('rsi', 0),
                                'sentiment': sentiment,
                                'atr': latest.get('atr', 0)
                            }
                        }
                        self.db.log_trade(trade_record)
                        self.risk_manager.update_daily_risk(config.BASE_RISK_PER_TRADE * max_score)
                else:
                    print("  [Risk] Trade rejected (Size 0)")
            else:
                print(f"  [Wait] No consensus for {symbol} (Winner: {winner} score {max_score:.2f} < 0.40)")

    def start(self):
        print("System Started. Press Ctrl+C to stop.")
        try:
            while True:
                self.run_cycle()
                print("\n[Sleep] Waiting 60 seconds...")
                time.sleep(60)
        except KeyboardInterrupt:
            print("Stopping...")
            mt5.shutdown()

if __name__ == "__main__":
    bot = TradingBot()
    bot.start()