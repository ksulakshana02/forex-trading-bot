import MetaTrader5 as mt5
import time

class TradeExecutor:
    def execute_trade(self, symbol, direction, lots, sl, tp, strategy_name, confidence):
        """
        Execute trade on MT5
        """
        price = mt5.symbol_info_tick(symbol).ask if direction == "BUY" else mt5.symbol_info_tick(symbol).bid
        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        
        # Determine correct filling mode
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"[Exec] Failed to get symbol info for {symbol}")
            return None
            
        filling_mode = mt5.ORDER_FILLING_FOK
        # 1 = FOK, 2 = IOC
        if symbol_info.filling_mode & 1:
            filling_mode = mt5.ORDER_FILLING_FOK
        elif symbol_info.filling_mode & 2:
            filling_mode = mt5.ORDER_FILLING_IOC
        else:
            filling_mode = mt5.ORDER_FILLING_RETURN
            
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
            "comment": f"{strategy_name[:10]} ({confidence:.2f})",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        
        # Retry logic
        for i in range(3):
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[Exec] {direction} {symbol} | Lots: {lots} | Price: {price}")
                return result
            elif result.retcode == mt5.TRADE_RETCODE_REQUOTE:
                time.sleep(0.5)
                continue
            else:
                print(f"[Exec] FAILED to execute: {result.comment}")
                return result
                
        return None
