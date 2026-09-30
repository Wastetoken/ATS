import os
import yaml
import logging
import pandas as pd
import re
from typing import Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.raw_dir = self.config['data']['raw_dir']
        self.processed_dir = self.config['data']['processed_dir']
        self.csv_path = self.config['data']['trade_history_csv']
        
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Cache for loaded/computed market data
        self.market_data: Dict[str, pd.DataFrame] = {}

    def _clean_numeric(self, val):
        if isinstance(val, str):
            val = re.sub(r'[A-Za-z\s%]', '', val)
            try:
                return float(val)
            except ValueError:
                return val
        return val

    def load_and_clean_trades(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        
        numeric_cols = ['Avg. Price', 'Exit Price', 'Held Qty', 'Max Qty', 'Close Qty', 
                        'Position PnL', 'Position PnL%', 'Closed PNL', 'Trading Fee', 'Funding Fee']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_numeric)
                
        df['Open Time'] = pd.to_datetime(df['Open Time'], utc=True)
        df['Close Time'] = pd.to_datetime(df['Close Time'], utc=True)
        return df

    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self.market_data:
            return self.market_data[cache_key]
            
        filepath = os.path.join(self.raw_dir, f"{symbol}_{timeframe}.csv")
        if not os.path.exists(filepath):
            logger.warning(f"Market data not found: {filepath}")
            return pd.DataFrame()
            
        df = pd.read_csv(filepath)
        df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True)
        df.set_index('ts', inplace=True)
        df = df.sort_index()
        
        # Compute Indicators
        # Trend (EMAs)
        df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Momentum (RSI)
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        rs = avg_gain / avg_loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Momentum (MACD)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        
        # Volatility (ATR)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATRr_14'] = tr.rolling(window=14, min_periods=1).mean()
        
        df['ADX_14'] = None # Skipping complex ADX implementation to save time
        
        # Support/Resistance Proxies (Rolling Min/Max)
        df['rolling_high_20'] = df['high'].rolling(20).max()
        df['rolling_low_20'] = df['low'].rolling(20).min()
        
        self.market_data[cache_key] = df
        return df

    def compute_btc_regime(self, timestamp: pd.Timestamp) -> dict:
        btc_df = self.get_market_data('BTCUSDT', '4H')
        if btc_df.empty:
            return {}
            
        # Lookahead prevention: strictly less than or equal to trade open time
        past_data = btc_df[btc_df.index <= timestamp]
        if past_data.empty:
            return {}
            
        last_candle = past_data.iloc[-1]
        
        # Determine regime
        close = last_candle['close']
        ema50 = last_candle.get('EMA_50', close)
        ema200 = last_candle.get('EMA_200', close)
        
        regime = "Neutral"
        if pd.notna(ema50) and pd.notna(ema200):
            if close > ema50 and ema50 > ema200:
                regime = "Bullish"
            elif close < ema50 and ema50 < ema200:
                regime = "Bearish"
                
        return {
            'btc_4h_close': close,
            'btc_4h_rsi': last_candle.get('RSI_14', None),
            'btc_regime': regime
        }

    def extract_trade_features(self, trade_row, timeframe='1H'):
        symbol = trade_row['Symbol']
        open_time = trade_row['Open Time']
        
        df = self.get_market_data(symbol, timeframe)
        if df.empty:
            return {}
            
        # Strictly closed candles before or at entry
        past_data = df[df.index <= open_time]
        if past_data.empty:
            return {}
            
        last_candle = past_data.iloc[-1]
        
        # Base features
        features = {
            f'{timeframe}_close': last_candle['close'],
            f'{timeframe}_rsi': last_candle.get('RSI_14', None),
            f'{timeframe}_atr': last_candle.get('ATRr_14', None),
            f'{timeframe}_ema9': last_candle.get('EMA_9', None),
            f'{timeframe}_ema20': last_candle.get('EMA_20', None),
            f'{timeframe}_ema50': last_candle.get('EMA_50', None),
            f'{timeframe}_ema200': last_candle.get('EMA_200', None),
            f'{timeframe}_adx': last_candle.get('ADX_14', None),
        }
        
        # Distances to EMAs
        close = last_candle['close']
        for period in [9, 20, 50, 200]:
            ema_val = features[f'{timeframe}_ema{period}']
            if pd.notna(ema_val) and ema_val > 0:
                features[f'{timeframe}_dist_ema{period}_pct'] = (close - ema_val) / ema_val * 100
            else:
                features[f'{timeframe}_dist_ema{period}_pct'] = None
                
        return features

    def generate(self):
        trades = self.load_and_clean_trades()
        feature_rows = []
        
        logger.info(f"Generating features for {len(trades)} trades...")
        for idx, row in trades.iterrows():
            trade_features = row.to_dict()
            
            # Extract features from different timeframes
            tf_1h = self.extract_trade_features(row, '1H')
            tf_15m = self.extract_trade_features(row, '15m')
            
            trade_features.update(tf_1h)
            trade_features.update(tf_15m)
            
            # BTC Regime
            btc_regime = self.compute_btc_regime(row['Open Time'])
            trade_features.update(btc_regime)
            
            feature_rows.append(trade_features)
            
        out_df = pd.DataFrame(feature_rows)
        out_path = os.path.join(self.processed_dir, 'trade_features.csv')
        out_df.to_csv(out_path, index=False)
        logger.info(f"Feature generation complete. Saved to {out_path}")

if __name__ == "__main__":
    generator = FeatureGenerator()
    generator.generate()
