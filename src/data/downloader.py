import os
import time
import requests
import logging
import pandas as pd
from typing import List, Dict, Optional
import yaml
from datetime import timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BloFinDownloader:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.api_base = self.config['data']['api_base_url']
        self.cache_dir = self.config['data']['cache_dir']
        self.raw_dir = self.config['data']['raw_dir']
        self.rate_limit = self.config['data']['api_rate_limit']
        
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    def _sleep_for_rate_limit(self):
        time.sleep(1.0 / self.rate_limit)

    def fetch_candles(self, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> pd.DataFrame:
        """
        Fetch candles from BloFin API for a specific range.
        ts are in milliseconds.
        """
        all_candles = []
        current_after = end_ts + 1  # We want to fetch backwards from the end
        
        url = f"{self.api_base}/market/candles"
        
        # BloFin API requires symbols like "BTC-USDT" instead of "BTCUSDT"
        inst_id = symbol.replace("USDT", "-USDT")
        
        while True:
            params = {
                "instId": inst_id,
                "bar": timeframe,
                "limit": 1440,
                "after": str(current_after)
            }
            
            try:
                self._sleep_for_rate_limit()
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != "0":
                    logger.error(f"API Error for {symbol}: {data.get('msg')}")
                    break
                    
                candles = data.get("data", [])
                if not candles:
                    break
                    
                all_candles.extend(candles)
                
                last_ts = int(candles[-1][0])
                if last_ts <= start_ts:
                    break
                    
                current_after = last_ts
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {symbol}: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
                continue

        if not all_candles:
            return pd.DataFrame()

        df = pd.DataFrame(all_candles, columns=[
            "ts", "open", "high", "low", "close", "vol", "volCurrency", "volCurrencyQuote", "confirm"
        ])
        
        df["ts"] = pd.to_numeric(df["ts"])
        df = df[df["ts"] >= start_ts]
        df = df[df["ts"] <= end_ts]
        
        # Sort chronologically
        df = df.sort_values("ts").reset_index(drop=True)
        
        # Convert to floats
        for col in ["open", "high", "low", "close", "vol", "volCurrency", "volCurrencyQuote"]:
            df[col] = df[col].astype(float)
            
        return df

    def get_required_ranges(self, csv_path: str) -> Dict[str, tuple]:
        """
        Parse the position history CSV to determine the date range needed for each symbol.
        """
        df = pd.read_csv(csv_path)
        df['Open Time'] = pd.to_datetime(df['Open Time'], utc=True)
        df['Close Time'] = pd.to_datetime(df['Close Time'], utc=True)
        
        ranges = {}
        warm_up = timedelta(days=self.config['download']['warm_up_period_days'])
        post_analysis = timedelta(hours=self.config['download']['post_entry_analysis_hours'])
        
        for symbol in df['Symbol'].unique():
            symbol_df = df[df['Symbol'] == symbol]
            start = symbol_df['Open Time'].min() - warm_up
            end = symbol_df['Close Time'].max() + post_analysis
            
            # Convert to ms timestamps
            start_ms = int(start.timestamp() * 1000)
            end_ms = int(end.timestamp() * 1000)
            
            ranges[symbol] = (start_ms, end_ms)
            
        return ranges

    def download_all(self):
        csv_path = self.config['data']['trade_history_csv']
        if not os.path.exists(csv_path):
            logger.error(f"Trade history CSV {csv_path} not found.")
            return

        ranges = self.get_required_ranges(csv_path)
        timeframes = self.config['download']['timeframes']
        
        for symbol, (start_ts, end_ts) in ranges.items():
            for tf in timeframes:
                filename = f"{symbol}_{tf}.csv"
                filepath = os.path.join(self.raw_dir, filename)
                
                if os.path.exists(filepath):
                    logger.info(f"File {filepath} already exists. Skipping download.")
                    continue
                    
                logger.info(f"Downloading {symbol} {tf} from {pd.to_datetime(start_ts, unit='ms')} to {pd.to_datetime(end_ts, unit='ms')}")
                
                df = self.fetch_candles(symbol, tf, start_ts, end_ts)
                
                if not df.empty:
                    df.to_csv(filepath, index=False)
                    logger.info(f"Saved {len(df)} candles to {filepath}")
                else:
                    logger.warning(f"No data returned for {symbol} {tf}")

if __name__ == "__main__":
    downloader = BloFinDownloader()
    downloader.download_all()
