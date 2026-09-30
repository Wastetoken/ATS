# ATS Trading System Reverse-Engineering

This project reverse-engineers a high-win-rate trading system based on historical BloFin position data.

## Project Structure
- `data/`: Contains raw CSVs, downloaded market data, and caches.
- `src/`: Python source code for data acquisition, feature engineering, and analysis.
- `results/`: Output reports and validation metrics.

## Setup and Installation
1. Install Python 3.10+
2. Install dependencies: `pip install -r requirements.txt`
3. Configure settings in `config.yaml`

## Phases
1. **Trade-History Input**: Parse the original position history and resolve missing data.
2. **Market Data Source**: Download required candlesticks from BloFin public API.
3. **Feature Generation**: Compute price, trend, momentum, support/resistance, and volume features.
4. **Condition Discovery**: Analyze the measurable conditions surrounding historical trades.
5. **Backtesting & Pine Script**: Reconstruct the logic in Python and Pine Script for validation.

## Data Source
All market data is fetched from the **BloFin official public API** (https://docs.blofin.com/).
No API keys are required for market data endpoints.
