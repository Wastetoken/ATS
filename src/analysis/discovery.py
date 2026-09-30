import os
import pandas as pd
import logging
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConditionDiscovery:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.processed_dir = self.config['data']['processed_dir']
        self.results_dir = os.path.join("results", "condition_discovery")
        os.makedirs(self.results_dir, exist_ok=True)
        
    def discover(self):
        csv_path = os.path.join(self.processed_dir, 'trade_features.csv')
        if not os.path.exists(csv_path):
            logger.error(f"Features file {csv_path} not found.")
            return
            
        df = pd.read_csv(csv_path)
        
        # We need a binary outcome
        df['Win'] = df['Closed PNL'] > 0
        df['Loss'] = df['Closed PNL'] <= 0
        
        report_lines = ["# Condition Discovery Report\n"]
        report_lines.append(f"Total Trades Analyzed: {len(df)}")
        report_lines.append(f"Overall Win Rate: {df['Win'].mean():.2%}\n")
        
        # Conditions to test
        conditions = {
            "BTC Bullish": df['btc_regime'] == 'Bullish',
            "BTC Bearish": df['btc_regime'] == 'Bearish',
            "BTC Neutral": df['btc_regime'] == 'Neutral',
            "1H RSI > 50": df['1H_rsi'] > 50,
            "1H RSI < 50": df['1H_rsi'] < 50,
            "1H Close > EMA 50": df['1H_close'] > df['1H_ema50'],
            "1H Close < EMA 50": df['1H_close'] < df['1H_ema50'],
            "15m RSI > 50": df['15m_rsi'] > 50,
            "15m RSI < 50": df['15m_rsi'] < 50,
        }
        
        for name, cond in conditions.items():
            subset = df[cond]
            trades = len(subset)
            if trades < self.config['analysis']['min_condition_sample_size']:
                continue
                
            wins = subset['Win'].sum()
            losses = subset['Loss'].sum()
            win_rate = wins / trades if trades > 0 else 0
            avg_pnl = subset['Closed PNL'].mean()
            
            report_lines.append(f"### {name}")
            report_lines.append(f"- Trades: {trades}")
            report_lines.append(f"- Win Rate: {win_rate:.2%}")
            report_lines.append(f"- Wins: {wins}, Losses: {losses}")
            report_lines.append(f"- Average PnL: {avg_pnl:.2f} USDT\n")
            
        report_path = os.path.join(self.results_dir, "report.md")
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
            
        logger.info(f"Condition discovery report written to {report_path}")

if __name__ == "__main__":
    discovery = ConditionDiscovery()
    discovery.discover()
