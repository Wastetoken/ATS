import os
import pandas as pd
import logging
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PythonBacktester:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.features_path = os.path.join(self.config['data']['processed_dir'], 'trade_features.csv')
        self.results_dir = os.path.join("results", "backtests")
        os.makedirs(self.results_dir, exist_ok=True)
        
    def run(self):
        if not os.path.exists(self.features_path):
            logger.error("Features not found. Run generator first.")
            return
            
        df = pd.read_csv(self.features_path)
        
        # Create Win/Loss binary columns
        df['Win'] = df['Closed PNL'] > 0
        df['Loss'] = df['Closed PNL'] <= 0
        
        # We will backtest on the pre-generated features which reflect conditions at entry
        # The strategy logic: BTC Bullish AND 1H Close > 1H EMA 50 AND 15m RSI > 50
        
        long_signals = df[
            (df['btc_regime'] == 'Bullish') &
            (df['1H_close'] > df['1H_ema50']) &
            (df['15m_rsi'] > 50)
        ].copy()
        
        logger.info(f"Backtester found {len(long_signals)} qualifying trades based on historical rules.")
        
        # Evaluate performance of these simulated entries using their actual historical outcomes
        wins = long_signals['Win'].sum()
        losses = long_signals['Loss'].sum()
        total = wins + losses
        win_rate = wins / total if total > 0 else 0
        total_pnl = long_signals['Closed PNL'].sum()
        
        report = [
            "# Python Backtester Results\n",
            f"Total Trades Evaluated: {total}",
            f"Win Rate: {win_rate:.2%}",
            f"Total PnL: {total_pnl:.2f} USDT",
            f"Wins: {wins}",
            f"Losses: {losses}"
        ]
        
        out_path = os.path.join(self.results_dir, "backtest_summary.md")
        with open(out_path, "w") as f:
            f.write("\n".join(report))
            
        logger.info(f"Backtest summary written to {out_path}")

if __name__ == "__main__":
    bt = PythonBacktester()
    bt.run()
