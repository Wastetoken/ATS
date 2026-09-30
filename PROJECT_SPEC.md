# Trading System Reverse-Engineering Project

## 1. Project Objective

I have an existing trading system with approximately a **93% historical win rate**.

The objective is to reverse-engineer the actual market conditions surrounding that system's trades and determine what measurable conditions distinguish winning trades from losing trades.

This is a research and reconstruction project.

**Do not assume the existing system is a generic swing strategy. Do not invent a replacement strategy before analyzing the actual trade history.**

The final project should determine:

1. What the market looked like around each actual trade.
2. Which measurable conditions were associated with winners.
3. Which measurable conditions were associated with losers.
4. Which combinations of conditions have meaningful predictive/selection value.
5. Whether those conditions can be implemented in TradingView Pine Script v6.
6. Whether an independent Python backtester can reproduce the Pine behavior.
7. Which entry, SL, TP, trailing, and breakeven parameters produce robust positive PnL while maintaining a high win rate.
8. Whether the discovered behavior survives walk-forward and out-of-sample testing.

The objective is **not simply to maximize win rate**.

Evaluate win rate together with:

* Total PnL
* Profit factor
* Trade count
* Average trade
* Median trade
* Maximum drawdown
* Largest winner
* Largest loser
* Consecutive losses
* Holding time
* MFE
* MAE
* Stability across time
* Stability across market regimes
* Out-of-sample performance

---

# 2. Required Project Structure

Create and maintain a reproducible project containing, at minimum:

```text
PROJECT_SPEC.md
README.md
requirements.txt
config.yaml

data/
    raw/
    processed/
    cache/

src/
    data/
    features/
    analysis/
    backtest/
    optimization/

results/
    data_quality/
    feature_analysis/
    condition_discovery/
    backtests/
    optimization/
    validation/
```

Do not unnecessarily create everything immediately. Build components as the corresponding project phase begins.

---

# 3. Reproducibility

Create a `config.yaml` containing configurable settings such as:

* Data source
* Symbols
* Timeframes
* Warm-up period
* Post-entry analysis period
* API limits
* Cache location
* Feature lookbacks
* Minimum condition sample size
* Maximum condition-combination depth
* Validation periods
* Backtest assumptions
* Commission
* Slippage
* Optimization ranges
* Random seeds where applicable

Create `requirements.txt`.

Create `README.md` documenting:

* Installation
* Configuration
* Run order
* Data sources
* Cache behavior
* Generated files
* Analysis methodology
* Backtest methodology
* Validation methodology

Every research result should be reproducible from the saved data and configuration.

---

# 4. Trade-History Input

The primary input is a CSV containing the trading history of the existing system.

Do not assume the column names.

Inspect the CSV programmatically.

Identify:

* Symbol
* Direction
* Entry timestamp
* Exit timestamp
* Entry price
* Exit price
* Quantity
* Position size
* Leverage
* Realized PnL
* Fees
* Trade ID
* Order ID
* Any fill ID
* Any other useful information

Preserve the original CSV.

Do not modify the source file.

Normalize timestamps into UTC while retaining the original timestamp information where useful.

---

# 5. Fills vs. Round-Trip Trades

This is critical.

Determine whether CSV rows represent:

* Complete round-trip trades
* Individual fills
* Partial entries
* Partial exits
* Scale-ins
* Scale-outs
* Averaging down
* Averaging up
* Position reversals

Do not assume each CSV row is one independent trade.

If multiple fills belong to one position, reconstruct the position/round-trip trade before performing winner/loser analysis.

Document the aggregation methodology.

If the data cannot unambiguously determine how fills belong to positions, report the ambiguity instead of silently guessing.

Also calculate:

* Average winner size
* Median winner size
* Average loser size
* Median loser size
* Winner/loss magnitude distribution
* Holding-time distribution
* PnL distribution

Specifically investigate whether a very high win rate is accompanied by relatively small winners and rare large losses.

---

# 6. Market Data Source

The primary market-data source is the **official BloFin public API** because the trade history originates from BloFin.

Official documentation:

https://docs.blofin.com/

Before implementing the downloader, inspect the current official BloFin API documentation and determine the correct public historical candlestick/OHLCV endpoints.

Do not invent endpoints.

Do not rely on undocumented endpoints.

Use only public market-data endpoints.

**Do not ask for API keys.**

Internet access is required to read the official documentation and retrieve public market data.

Use the actual symbols from the trade CSV.

Use the actual traded instrument whenever possible.

For BTC market-regime analysis, retrieve the relevant BTC-USDT perpetual market data from BloFin whenever available.

---

# 7. Insufficient BloFin Data

Do not silently substitute another exchange.

BloFin may not provide sufficient historical depth for some symbols or small timeframes such as 1-minute candles.

If BloFin cannot supply the required historical data for a symbol or timeframe:

1. Stop the affected data-acquisition step.
2. Report exactly:

   * Symbol
   * Timeframe
   * Required date range
   * Available date range
   * Missing period
   * API limitation or other reason
3. Do not fabricate candles.
4. Do not silently use another exchange.
5. Ask me for approval before using a fallback source.

If I approve a fallback, clearly record the fallback source in the dataset.

---

# 8. Optional BTC Fallback

If and only if I approve a fallback for missing BTC data, Binance public BTCUSDT historical market data may be used.

Official Binance documentation:

https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints

Clearly record:

```text
data_source = BINANCE
```

Do not silently mix BloFin and Binance data.

The source exchange must always be retained as metadata.

---

# 9. Market Data Acquisition

Retrieve sufficient OHLCV/candlestick history to reconstruct market conditions around every trade.

Required considerations:

* Pre-entry warm-up
* Pre-entry feature windows
* Entry candle
* Post-entry trade path
* MFE
* MAE
* Time-to-MFE
* Time-to-MAE

Investigate these timeframes where data availability permits:

* 1m
* 5m
* 15m
* 30m
* 1h
* 2h
* 4h
* 6h
* 12h
* 1d

Do not download enormous datasets unnecessarily.

Determine the minimum history required from the actual trade timestamps and feature lookbacks.

---

# 10. Downloader Requirements

The downloader must:

* Read symbols from the CSV.
* Determine required date ranges.
* Handle API pagination.
* Respect API rate limits.
* Retry temporary failures.
* Use exponential backoff.
* Cache downloaded candles.
* Resume interrupted downloads.
* Avoid duplicate downloads.
* Preserve raw data.
* Normalize timestamps.
* Sort chronologically.
* Detect duplicates.
* Detect gaps.
* Detect invalid OHLC relationships.
* Detect timestamp anomalies.
* Never fabricate missing candles.

Raw market data must remain separate from processed feature data.

---

# 11. Lookahead Prevention

Every feature must represent information that would have been available at the actual trade-entry time.

Do not use future candles.

Pay particular attention to:

* Current versus closed candles
* Higher-timeframe candles
* `request.security()` equivalent behavior
* Candle boundaries
* Timezone conversion
* Intrabar information
* Future highs/lows
* Future support/resistance confirmation

When a feature requires confirmation from a future candle, it must not be available to the historical entry.

Document these decisions.

---

# 12. Trade-Level Feature Dataset

Create one primary trade-level dataset where each row represents a reconstructed round-trip position.

Include the original trade information plus market-state features.

---

# 13. Price and Volatility Features

Investigate:

* Price returns
* ATR
* ATR%
* Realized volatility
* Candle range
* Candle body
* Upper wick
* Lower wick
* Body/range ratio
* Volatility expansion
* Volatility contraction
* Recent high
* Recent low
* Rolling highs
* Rolling lows
* Local swing highs
* Local swing lows
* Distance to highs/lows
* Distances in percentage terms
* Distances in ATR units

Use multiple sensible lookbacks.

---

# 14. Trend Features

Investigate:

* EMA 9
* EMA 20
* EMA 21
* EMA 50
* EMA 100
* EMA 200
* SMA equivalents where useful
* Price/EMA distance
* EMA slopes
* EMA alignment
* Trend direction
* Trend strength
* Pullback depth
* ATR-normalized distance

Do not assume any specific indicator is useful.

Measure its relationship to actual trade outcomes.

---

# 15. Momentum Features

Investigate:

* RSI
* RSI slope
* RSI change
* MACD
* MACD histogram
* ROC
* Momentum
* ADX
* +DI
* -DI

Again, preserve raw numerical values.

Do not rely only on categorical labels.

---

# 16. Support and Resistance

Support/resistance is a major research area.

Investigate:

* Recent swing highs/lows
* Rolling support/resistance
* Previous day high/low
* Previous week high/low
* Consolidation ranges
* Repeatedly tested levels
* Touch count
* Time since touch
* Breaks
* Sweeps
* Reclaims
* Rejections
* Distance to nearest support
* Distance to nearest resistance
* Percentage distance
* ATR-normalized distance

For long trades, analyze behavior around support and resistance.

For short trades, analyze the equivalent structure.

Do not label a trade a bounce simply because a level exists nearby.

Measure the actual price behavior.

---

# 17. Price-Action Windows

Analyze pre-entry windows such as:

* 5 candles
* 10 candles
* 20 candles
* 50 candles
* 100 candles

Where useful, perform this across multiple timeframes.

Investigate:

* Trend into level
* Pullback
* Consolidation
* Compression
* Expansion
* Rejection
* Sweep
* Failed breakout
* Breakout
* Reclaim
* Higher highs
* Higher lows
* Lower highs
* Lower lows
* Momentum exhaustion
* Wick rejection
* Consecutive directional candles

Convert qualitative concepts into quantitative features wherever possible.

---

# 18. Volume Features

Investigate:

* Raw volume
* Volume moving averages
* Relative volume
* Volume spikes
* Volume expansion
* Volume contraction
* Volume during rejection
* Volume during breakout
* Volume relative to preceding trend

---

# 19. BTC Regime

For every trade, reconstruct the BTC market environment.

Use BloFin BTC-USDT perpetual data when available.

Investigate:

* BTC 1h return
* BTC 4h return
* BTC 12h return
* BTC 24h return
* BTC ATR
* BTC ATR%
* BTC volatility
* BTC EMA 20
* BTC EMA 50
* BTC EMA 200
* BTC EMA slopes
* BTC RSI
* BTC momentum
* BTC recent high/low
* BTC drawdown
* BTC support/resistance
* BTC volume
* BTC relative volume

Create measurable BTC regime classifications where useful:

* Bullish
* Bearish
* Neutral/ranging
* High volatility
* Low volatility
* Volatility expansion
* Volatility contraction

Always retain the underlying numerical features.

---

# 20. Trade-Path Analysis

Calculate:

* MFE
* MAE
* Maximum favorable percentage movement
* Maximum adverse percentage movement
* Time to MFE
* Time to MAE
* MFE in ATR units
* MAE in ATR units
* Initial movement after entry
* Whether the position initially moved against entry
* Recovery behavior
* Time spent profitable
* Time spent adverse

This analysis will later inform:

* Stop loss
* Take profit
* Trailing stop
* Breakeven
* Maximum holding time

---

# 21. Winner vs. Loser Analysis

Compare winners and losers for every meaningful feature.

Calculate:

* Sample size
* Mean
* Median
* Standard deviation
* Percentiles
* Minimum
* Maximum
* Win rate
* Average PnL
* Median PnL
* Total PnL

Do not rely solely on correlation.

A feature is only useful for strategy selection if it produces meaningful behavior when used to select trades.

---

# 22. Condition Discovery

Discover combinations of conditions rather than assuming them.

Investigate combinations involving:

* Support/resistance
* Sweeps
* Reclaims
* Rejections
* RSI
* Momentum
* EMA structure
* Trend
* ATR
* Volatility
* Volume
* Price action
* BTC regime
* BTC momentum
* BTC volatility
* Multi-timeframe agreement

For each candidate condition report:

* Trades
* Wins
* Losses
* Win rate
* Total PnL
* Average PnL
* Median PnL
* Profit factor
* Maximum drawdown
* Largest winner
* Largest loser

---

# 23. Multiple-Testing Control

The feature-discovery stage can easily generate false edges.

Therefore:

* Define a minimum trade count for candidate conditions.
* Do not accept tiny samples merely because their win rate is high.
* Limit maximum combination depth.
* Record the number of candidate conditions tested.
* Record the number of combinations tested.
* Avoid unrestricted brute-force searches across thousands of arbitrary thresholds.
* Distinguish exploratory findings from validated findings.

If a result is statistically interesting but based on insufficient data, label it accordingly.

---

# 24. Walk-Forward Validation

Use chronological validation.

Do not rely solely on one train/test split.

For strategy and parameter optimization, use walk-forward testing where practical:

1. Train/optimize on an earlier period.
2. Validate on the immediately following period.
3. Roll the window forward.
4. Repeat.
5. Aggregate out-of-sample results.

Do not randomly shuffle the time series for primary validation.

Report both in-sample and out-of-sample results.

---

# 25. Pine Script Stage

Only after the market-data reconstruction and condition-discovery stages are complete should Pine Script v6 be created.

Build the strategy from the conditions supported by the research.

Do not replace the discovered behavior with a generic strategy.

If I provide an existing Pine strategy, inspect it first.

Reuse its relevant structure and inputs where appropriate, including existing parameters such as:

```text
trailTriggerPctInput
trailOffsetPctInput
```

Do not arbitrarily remove existing useful logic.

---

# 26. Python Backtester

Create an independent Python backtester implementing the same strategy logic.

Model:

* Entries
* Long/short direction
* Position sizing
* Commission
* Slippage
* Stop loss
* Take profit
* Trailing stop
* Breakeven
* Exit timing
* Candle execution assumptions
* Intrabar assumptions where relevant

The Python backtester must not simply copy TradingView's reported results.

It must independently calculate the results.

---

# 27. TradingView Data-Feed Matching

Before comparing Python with TradingView, verify that the instruments/data feeds actually correspond.

Confirm:

* TradingView symbol
* Exchange
* Contract type
* Perpetual versus spot
* OHLCV source
* Timezone
* Candle boundaries
* Historical date range

BloFin candles and TradingView candles may not be identical.

If they differ, quantify and document the discrepancy.

Do not treat different market feeds as an implementation bug without first checking the underlying data.

---

# 28. Python vs TradingView Comparison

Compare:

* Number of trades
* Entry timestamps
* Entry prices
* Exit timestamps
* Exit prices
* Winners/losses
* Total PnL
* Commission
* Maximum drawdown

When results differ, investigate:

* Candle data
* Timezone
* Candle boundaries
* Intrabar execution
* `process_orders_on_close`
* Stop/target execution
* Trailing behavior
* Breakeven behavior
* Higher-timeframe calculations
* Lookahead
* Rounding
* Commission
* Slippage

Do not simply adjust Python until it matches without identifying why.

---

# 29. Parameter Optimization

After the strategy is implemented, optimize its parameters in Python.

Investigate:

## Stop loss

* Percentage
* ATR multiplier
* Structure-based distance

## Take profit

* Percentage
* R multiple
* ATR multiplier

## Trailing

Specifically test:

* `trailTriggerPctInput`
* `trailOffsetPctInput`

Also test:

* Activation threshold
* Trailing distance
* ATR-based trailing
* Structure-based trailing

## Breakeven

Test:

* Activation threshold
* Offset
* R-based activation
* ATR-based activation

## Entry

Where supported by the discovered edge, investigate:

* Support distance
* Resistance distance
* ATR multipliers
* RSI thresholds
* EMA distances
* Momentum thresholds
* BTC regime thresholds
* BTC volatility thresholds
* Volume thresholds
* Confirmation requirements
* Rejection thresholds
* Lookback periods

---

# 30. Fine-Grained Optimization

Do not restrict optimization to arbitrary whole-percentage increments.

If the useful region is around 0.5% to 1.0%, test fine increments such as:

```text
0.50%
0.51%
0.52%
0.53%
...
1.00%
```

Use sensible precision for each parameter.

However, do not blindly test every possible combination.

Use the earlier research to narrow the search space.

---

# 31. Optimization Objective

Do not optimize exclusively for:

* Win rate
* PnL
* Trade count

Evaluate them jointly with:

* Profit factor
* Maximum drawdown
* Average trade
* Median trade
* Trade count
* Largest winner
* Largest loser
* Stability
* Walk-forward performance
* Out-of-sample performance

Identify robust regions rather than only one historical optimum.

If several parameter sets perform similarly, investigate whether performance remains strong across a range of neighboring values.

A narrow spike in performance is a potential overfitting warning.

---

# 32. Required Reports

Produce:

## Data-quality report

* Symbols
* Timeframes
* Sources
* Date ranges
* Candle counts
* Missing candles
* Duplicates
* Invalid candles
* API limitations

## Trade reconstruction report

* Original rows
* Reconstructed positions
* Fills
* Partial entries/exits
* Scale-ins/scale-outs
* Winner/loser statistics
* Holding-time distribution

## Feature report

* Feature
* Winner statistics
* Loser statistics
* PnL relationship
* Sample size

## Condition-discovery report

* Condition
* Trade count
* Win rate
* PnL
* Profit factor
* Drawdown
* Validation performance

## Optimization report

* Parameter values
* Trade count
* Win rate
* PnL
* Profit factor
* Drawdown
* In-sample performance
* Out-of-sample performance
* Walk-forward performance

---

# 33. Final Deliverables

The completed project should contain:

1. Raw market-data downloader
2. Market-data cache
3. Trade reconstruction
4. Feature-engineering pipeline
5. Winner/loser analysis
6. Condition-discovery system
7. Walk-forward validation
8. Pine Script v6 strategy
9. Independent Python backtester
10. Parameter optimizer
11. Python/TradingView comparison
12. Reproducible configuration
13. README
14. Requirements file
15. Research result files

---

# 34. Absolute Rules

Never:

* Invent market data.
* Fabricate candles.
* Invent BloFin endpoints.
* Silently switch exchanges.
* Ask for private API keys when public data is sufficient.
* Use future information.
* Hide losing trades.
* Delete inconvenient outliers without documenting why.
* Declare an edge from a tiny sample.
* Optimize solely for win rate.
* Optimize solely for PnL.
* Build a generic strategy before analyzing the original trades.
* Randomly shuffle time-series data for primary validation.
* Claim robustness without out-of-sample evidence.

Always:

* Preserve source data.
* Preserve raw market data.
* Record data source.
* Record timestamps.
* Record timeframes.
* Cache downloaded data.
* Document transformations.
* Quantify sample sizes.
* Record multiple-testing scope.
* Use chronological validation.
* Separate exploration from validation.
* Make the research reproducible.

---

# 35. Project Checkpoints

This project is intentionally divided into checkpoints.

**Never automatically proceed through all phases.**

At the end of each checkpoint:

1. Complete only the requested phase.
2. Produce its report/results.
3. Explain what was found.
4. Identify any blockers or data limitations.
5. Stop.
6. Wait for my approval before proceeding to the next phase.

Do not interpret "then continue" or similar wording inside this specification as permission to bypass the checkpoint system.

---

# PHASES

## Phase 1

Inspect and validate the trade-history CSV.

## Phase 2

Determine the correct BloFin public API endpoints and establish the market-data acquisition plan.

## Phase 3

Download and validate the required BloFin market data.

## Phase 4

Reconstruct positions and build the trade-level feature dataset.

## Phase 5

Analyze winners versus losers.

## Phase 6

Discover candidate market-condition combinations.

## Phase 7

Perform chronological and walk-forward validation.

## Phase 8

Build the Pine Script v6 implementation.

## Phase 9

Build the independent Python backtester.

## Phase 10

Verify Python versus TradingView.

## Phase 11

Perform fine-grained parameter optimization.

## Phase 12

Perform final walk-forward/out-of-sample validation and produce final deliverables.

---

# CURRENT PHASE RULE

When I tell you to perform a phase, perform **only that phase**.

Do not begin the next phase automatically.

At the end, stop and wait for my explicit instruction.
