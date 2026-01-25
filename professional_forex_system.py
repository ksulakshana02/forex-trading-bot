"""
PROFESSIONAL MULTI-STRATEGY FOREX TRADING SYSTEM
Based on Renaissance Technologies' principles and modern ML research

Key Philosophy:
- Target 55-65% win rate (realistic, not fantasy 80-100%)
- Multiple uncorrelated strategies
- Small edges compounded through volume and consistency
- Risk management > prediction accuracy
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

# === CONFIGURATION ===
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]  # Diversification
TIMEFRAME = mt5.TIMEFRAME_H1  # More reliable than M15
BASE_RISK_PER_TRADE = 0.005  # 0.5% per trade
MAX_DAILY_RISK = 0.02  # 2% total daily risk
TARGET_SHARPE = 1.5  # Realistic institutional target

class ProfessionalTradingSystem:
    def __init__(self):
        """Initialize the professional trading system"""
        if not mt5.initialize():
            raise Exception("MT5 initialization failed")
        
        # Enable all symbols
        for symbol in SYMBOLS:
            if not mt5.symbol_select(symbol, True):
                print(f"Warning: Could not enable {symbol}")
        
        self.account_start = mt5.account_info().equity
        self.daily_risk_used = 0.0
        self.trade_history = []
        
        # Strategy allocations (uncorrelated strategies)
        self.strategies = {
            'statistical_arbitrage': 0.30,  # Mean reversion
            'momentum_breakout': 0.25,       # Trend following
            'volatility_regime': 0.20,       # Volatility-based
            'ml_ensemble': 0.25              # Machine learning
        }
        
        print("[✓] Professional System Initialized")
        print(f"[✓] Target Win Rate: 55-65% (Realistic)")
        print(f"[✓] Strategy: Multiple Uncorrelated Edges")
        print(f"[✓] Risk Per Trade: {BASE_RISK_PER_TRADE*100}%")
        
    
    def get_market_data(self, symbol, lookback=500):
        """Fetch and process market data with advanced features"""
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, lookback)
        if rates is None or len(rates) < lookback:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Technical indicators (multiple timeframes)
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        df['bb_mid'] = bb['BBM_20_2.0']
        
        # MACD
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        
        # ADX for trend strength
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx['ADX_14']
        
        # Volatility metrics
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_ratio'] = df['atr'] / df['close']
        
        return df.dropna()
    
    
    def strategy_statistical_arbitrage(self, df):
        """
        Strategy 1: Statistical Arbitrage (Mean Reversion)
        Trades when price deviates significantly from statistical mean
        """
        latest = df.iloc[-1]
        
        # Z-score calculation
        mean_price = df['close'].rolling(100).mean().iloc[-1]
        std_price = df['close'].rolling(100).std().iloc[-1]
        z_score = (latest['close'] - mean_price) / std_price
        
        # RSI confirmation
        rsi_oversold = latest['rsi'] < 30
        rsi_overbought = latest['rsi'] > 70
        
        signal = None
        confidence = 0
        
        # Mean reversion logic
        if z_score < -2.0 and rsi_oversold:  # Oversold
            signal = "BUY"
            confidence = min(abs(z_score) / 3.0, 1.0)
        elif z_score > 2.0 and rsi_overbought:  # Overbought
            signal = "SELL"
            confidence = min(abs(z_score) / 3.0, 1.0)
        
        return signal, confidence
    
    
    def strategy_momentum_breakout(self, df):
        """
        Strategy 2: Momentum Breakout
        Captures strong trends with ADX confirmation
        """
        latest = df.iloc[-1]
        
        # Trend confirmation with multiple EMAs
        ema_aligned_up = (latest['ema_20'] > latest['ema_50'] > latest['ema_200'])
        ema_aligned_down = (latest['ema_20'] < latest['ema_50'] < latest['ema_200'])
        
        # Strong trend (ADX > 25)
        strong_trend = latest['adx'] > 25
        
        # MACD confirmation
        macd_bullish = latest['macd'] > latest['macd_signal']
        macd_bearish = latest['macd'] < latest['macd_signal']
        
        signal = None
        confidence = 0
        
        if ema_aligned_up and strong_trend and macd_bullish:
            signal = "BUY"
            confidence = min(latest['adx'] / 50.0, 1.0)
        elif ema_aligned_down and strong_trend and macd_bearish:
            signal = "SELL"
            confidence = min(latest['adx'] / 50.0, 1.0)
        
        return signal, confidence
    
    
    def strategy_volatility_regime(self, df):
        """
        Strategy 3: Volatility Regime Trading
        Adapts to market volatility conditions
        """
        latest = df.iloc[-1]
        
        # Volatility percentile
        vol_percentile = (df['volatility_20'].rank(pct=True).iloc[-1])
        
        # Bollinger Band position
        bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        
        signal = None
        confidence = 0
        
        # Low volatility mean reversion
        if vol_percentile < 0.3:  # Low vol regime
            if bb_position < 0.2:  # Near lower band
                signal = "BUY"
                confidence = 0.7
            elif bb_position > 0.8:  # Near upper band
                signal = "SELL"
                confidence = 0.7
        
        # High volatility trend following
        elif vol_percentile > 0.7:  # High vol regime
            if latest['close'] > latest['bb_upper'] and latest['rsi'] > 50:
                signal = "BUY"
                confidence = 0.6
            elif latest['close'] < latest['bb_lower'] and latest['rsi'] < 50:
                signal = "SELL"
                confidence = 0.6
        
        return signal, confidence
    
    
    def strategy_ml_ensemble(self, df):
        """
        Strategy 4: Machine Learning Ensemble
        Uses Random Forest for pattern recognition
        """
        # Prepare features
        feature_cols = ['rsi', 'macd', 'adx', 'volatility_20', 'volatility_ratio']
        
        # Create target (1 = up, 0 = down in next 4 hours)
        df['target'] = (df['close'].shift(-4) > df['close']).astype(int)
        
        # Training data (last 300 bars)
        train_df = df.iloc[-304:-4].copy()
        
        if len(train_df) < 100:
            return None, 0
        
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df['target']
        
        # Train Random Forest
        try:
            rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            rf.fit(X_train, y_train)
            
            # Predict current
            X_current = df[feature_cols].iloc[-1:].fillna(0)
            prediction = rf.predict(X_current)[0]
            confidence = rf.predict_proba(X_current)[0].max()
            
            signal = "BUY" if prediction == 1 else "SELL"
            
            # Only trade if confidence > 60%
            if confidence < 0.60:
                return None, 0
            
            return signal, confidence - 0.5  # Adjust confidence
        except:
            return None, 0
    
    
    def aggregate_signals(self, symbol):
        """
        Aggregate all strategy signals with weights
        This is similar to Renaissance's multi-signal approach
        """
        df = self.get_market_data(symbol)
        if df is None or len(df) < 200:
            return None
        
        signals = {}
        
        # Run all strategies
        signals['stat_arb'] = self.strategy_statistical_arbitrage(df)
        signals['momentum'] = self.strategy_momentum_breakout(df)
        signals['volatility'] = self.strategy_volatility_regime(df)
        signals['ml'] = self.strategy_ml_ensemble(df)
        
        # Weighted voting system
        buy_score = 0
        sell_score = 0
        
        for strategy_name, (signal, confidence) in signals.items():
            weight = self.strategies.get(strategy_name.replace('_', '_'), 0.25)
            
            if signal == "BUY":
                buy_score += confidence * weight
            elif signal == "SELL":
                sell_score += confidence * weight
        
        # Decision threshold (requires >40% weighted confidence)
        threshold = 0.40
        
        if buy_score > threshold and buy_score > sell_score:
            return "BUY", buy_score, df
        elif sell_score > threshold and sell_score > buy_score:
            return "SELL", sell_score, df
        
        return None
    
    
    def calculate_position_size(self, symbol, sl_distance, confidence):
        """
        Kelly Criterion-inspired position sizing with confidence scaling
        """
        account = mt5.account_info()
        balance = account.balance
        
        # Base risk adjusted by confidence (0.5% to 1.0%)
        risk_percent = BASE_RISK_PER_TRADE * (0.5 + confidence)
        
        # Check daily risk limit
        if self.daily_risk_used >= MAX_DAILY_RISK:
            return 0.0
        
        risk_amount = balance * risk_percent
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.0
        
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        
        if tick_size == 0 or tick_value == 0:
            return 0.01
        
        lots = risk_amount / ((sl_distance / tick_size) * tick_value)
        
        # Normalize
        step = symbol_info.volume_step
        lots = round(lots / step) * step
        lots = max(symbol_info.volume_min, min(lots, symbol_info.volume_max))
        
        return lots
    
    
    def execute_trade(self, symbol, direction, confidence, df):
        """Execute trade with proper risk management"""
        latest = df.iloc[-1]
        price = latest['close']
        atr = latest['atr']
        
        # Dynamic SL/TP based on ATR and volatility regime
        volatility_mult = 1.5 if latest['adx'] > 25 else 2.0
        
        sl_distance = atr * volatility_mult
        tp_distance = atr * volatility_mult * 2.5  # 2.5:1 reward ratio minimum
        
        lots = self.calculate_position_size(symbol, sl_distance, confidence)
        
        if lots == 0:
            print(f"   ⚠️ Risk limit reached for {symbol}")
            return
        
        if direction == "BUY":
            sl = price - sl_distance
            tp = price + tp_distance
            order_type = mt5.ORDER_TYPE_BUY
        else:
            sl = price + sl_distance
            tp = price - tp_distance
            order_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lots),
            "type": order_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 123456,
            "comment": f"Multi-Strat ({confidence:.2f})",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        print(f"\n[{symbol}] {direction} Signal | Confidence: {confidence:.2%}")
        print(f"   Risk: {lots} lots | SL: {sl:.5f} | TP: {tp:.5f}")
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   ✅ ORDER EXECUTED")
            self.daily_risk_used += BASE_RISK_PER_TRADE * confidence
        else:
            print(f"   ❌ FAILED: {result.comment}")
    
    
    def run(self):
        """Main trading loop"""
        print("\n=== PROFESSIONAL MULTI-STRATEGY SYSTEM ACTIVE ===\n")
        
        last_check = {}
        
        while True:
            try:
                current_time = datetime.now()
                
                # Reset daily risk at market open
                if current_time.hour == 0 and current_time.minute < 5:
                    self.daily_risk_used = 0.0
                    print("[✓] Daily risk counter reset")
                
                # Scan all symbols
                for symbol in SYMBOLS:
                    # Cooldown (1 hour between checks per symbol)
                    if symbol in last_check:
                        if (current_time - last_check[symbol]).seconds < 3600:
                            continue
                    
                    result = self.aggregate_signals(symbol)
                    
                    if result:
                        direction, confidence, df = result
                        self.execute_trade(symbol, direction, confidence, df)
                        last_check[symbol] = current_time
                
                # Performance reporting
                if current_time.minute == 0:  # Every hour
                    equity = mt5.account_info().equity
                    pnl_pct = ((equity - self.account_start) / self.account_start) * 100
                    print(f"\n[{current_time.strftime('%H:%M')}] P&L: {pnl_pct:+.2f}% | Risk Used: {self.daily_risk_used*100:.1f}%")
                
                import time
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nShutting down system...")
                mt5.shutdown()
                break
            except Exception as e:
                print(f"Error: {e}")
                import time
                time.sleep(60)


if __name__ == "__main__":
    system = ProfessionalTradingSystem()
    system.run()
