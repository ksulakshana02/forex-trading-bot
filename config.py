import MetaTrader5 as mt5

# === TRADING CONFIGURATION ===
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD"]  # Expanded diversification
TIMEFRAME = mt5.TIMEFRAME_H1
MAGIC_NUMBER = 123456

# === RISK MANAGEMENT ===
BASE_RISK_PER_TRADE = 0.005  # 0.5% per trade
MAX_DAILY_RISK = 0.02  # 2% total daily risk
TARGET_SHARPE = 1.5
MAX_CORRELATION = 0.7  # Max allowed correlation between active pairs

# === STRATEGY ALLOCATION ===
STRATEGY_WEIGHTS = {
    'statistical_arbitrage': 0.20,
    'momentum_breakout': 0.20,
    'volatility_regime': 0.15,
    'ml_ensemble': 0.20,
    'fundamental': 0.30
}

# === DATABASE ===
DB_PATH = "trading_history.db"
