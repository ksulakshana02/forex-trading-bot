import sqlite3
import pandas as pd
from datetime import datetime
import config

class DatabaseHandler:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket INTEGER,
            symbol TEXT,
            strategy TEXT,
            direction TEXT,
            entry_time TIMESTAMP,
            exit_time TIMESTAMP,
            entry_price REAL,
            exit_price REAL,
            sl REAL,
            tp REAL,
            volume REAL,
            profit REAL,
            commission REAL,
            swap REAL,
            pnl_net REAL,
            confidence REAL,
            regime TEXT,
            regime TEXT,
            status TEXT,
            metrics TEXT
        )
        ''')
        
        # Attempt migration for existing users
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN metrics TEXT")
        except:
            pass # Column likely exists
        
        # Daily Performance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            equity_start REAL,
            equity_end REAL,
            daily_return REAL,
            trades_count INTEGER,
            win_rate REAL,
            sharpe_ratio REAL,
            max_drawdown REAL
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"[Database] Initialized at {self.db_path}")

    def log_trade(self, trade_data):
        """Log a new trade or update existing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if ticket already exists
        cursor.execute('SELECT id FROM trades WHERE ticket = ?', (trade_data.get('ticket'),))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing trade (e.g. at exit)
            query = '''
            UPDATE trades SET 
                exit_time = ?, exit_price = ?, profit = ?, 
                commission = ?, swap = ?, pnl_net = ?, status = ?
            WHERE ticket = ?
            '''
            cursor.execute(query, (
                trade_data.get('exit_time'),
                trade_data.get('exit_price'),
                trade_data.get('profit'),
                trade_data.get('commission'),
                trade_data.get('swap'),
                trade_data.get('pnl_net'),
                trade_data.get('status'),
                trade_data.get('ticket')
            ))
        else:
            # Insert new trade
            query = '''
            INSERT INTO trades (
                ticket, symbol, strategy, direction, entry_time, 
                entry_price, sl, tp, volume, confidence, regime, status, metrics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                trade_data.get('ticket'),
                trade_data.get('symbol'),
                trade_data.get('strategy'),
                trade_data.get('direction'),
                trade_data.get('entry_time'),
                trade_data.get('entry_price'),
                trade_data.get('sl'),
                trade_data.get('tp'),
                trade_data.get('volume'),
                trade_data.get('confidence'),
                trade_data.get('regime'),
                'OPEN',
                str(trade_data.get('metrics', {}))
            ))
            
        conn.commit()
        conn.close()

    def get_trades_df(self):
        """Get trades as DataFrame for analysis"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
        return df

    def get_today_risk(self):
        """Calculate total risk used today (sum of initial risk of open/closed trades)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # We estimate risk used as: Sum of (Volume * Confidence * Base_Risk)? 
        # Actually, RiskManager tracks `daily_risk_used` as a running counter of % risk.
        # But for exact restart, we might just sum the 'pnl_net' of closed trades + current open risk?
        # A simpler approach for the 'Hard Cap' is to sum Realized Loss + Open Risk.
        
        # Let's approximate by summing the Net Loss of today's closed trades.
        today = datetime.now().date()
        query = "SELECT SUM(pnl_net) FROM trades WHERE DATE(exit_time) = ? AND pnl_net < 0"
        cursor.execute(query, (today,))
        realized_loss = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        # Note: accurate tracking requires storing 'risk_pct' per trade. 
        # For now, we return Realized Loss to check against Max Drawdown.
        return abs(realized_loss)

    def get_strategy_performance(self, lookback=50):
        """
        Calculate win rate for each strategy over the last N trades.
        Returns: Dict {strategy_name: win_rate}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last N closed trades
        query = '''
        SELECT strategy, pnl_net 
        FROM trades 
        WHERE status = 'CLOSED' 
        ORDER BY exit_time DESC 
        LIMIT ?
        '''
        cursor.execute(query, (lookback,))
        trades = cursor.fetchall()
        
        conn.close()
        
        if not trades:
            return {}
            
        stats = {}
        for strategy, pnl in trades:
            if strategy not in stats:
                stats[strategy] = {'wins': 0, 'total': 0}
            
            stats[strategy]['total'] += 1
            if pnl > 0:
                stats[strategy]['wins'] += 1
                
        # Calculate win rates
        win_rates = {}
        for strategy, data in stats.items():
            if data['total'] > 0:
                win_rates[strategy] = data['wins'] / data['total']
            else:
                win_rates[strategy] = 0.0
                
        return win_rates
