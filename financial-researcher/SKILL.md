---
name: financial-researcher
description: Professional-grade autonomous financial analyst leveraging 7 legendary investor perspectives (Buffett, Graham, Lynch, Wood, Soros, Dalio, Burry). Features Python processing layer for institutional-grade composite scores (Piotroski, Altman, Beneish). Guided by DRIVER methodology. For internal use - provides bold, forward-looking analysis.
version: 2.0.0
---

# Financial Researcher Skill

## Quick Reference

```
/financial-researcher AAPL          # Analyze Apple (prompts for mode)
/financial-researcher NVDA --full   # Force full analysis
/financial-researcher TSLA --quick  # Force quick lookup
```

---

## ORCHESTRATION OVERVIEW

This skill operates in two modes and follows the DRIVER methodology:

```
┌─────────────────────────────────────────────────────────────┐
│  USER: /financial-researcher {TICKER}                       │
├─────────────────────────────────────────────────────────────┤
│  1. MODE SELECTION                                          │
│     └─> Quick lookup OR Full 8-guru analysis                │
├─────────────────────────────────────────────────────────────┤
│  2. [DISCOVER] - Data Fetching                              │
│     ├─> Calculate data union based on mode                  │
│     ├─> Fetch from financialdatasets-mcp                    │
│     ├─> Fetch from tavily-mcp                               │
│     └─> Fetch 13-F holdings for relevant gurus              │
├─────────────────────────────────────────────────────────────┤
│  3. [PROCESS] - Python Metrics Calculation ⭐ NEW           │
│     ├─> Run processing.run_analysis() on raw data           │
│     ├─> Calculate composite scores (Piotroski, Altman, etc) │
│     ├─> Generate quality flags and warnings                 │
│     └─> Format LLM-ready context for each expert            │
├─────────────────────────────────────────────────────────────┤
│  4. [REPRESENT] - Planning                                  │
│     ├─> Map pre-calculated metrics to each expert           │
│     └─> Prepare dispatch parameters                         │
├─────────────────────────────────────────────────────────────┤
│  5. [IMPLEMENT] - Expert Dispatch (Full mode only)          │
│     └─> Spawn 7 Task subagents IN PARALLEL                  │
├─────────────────────────────────────────────────────────────┤
│  6. [VALIDATE] - Cross-Check                                │
│     └─> Verify all expert outputs, log failures             │
├─────────────────────────────────────────────────────────────┤
│  7. [EVOLVE] - Consolidation                                │
│     ├─> Tally signals                                       │
│     ├─> Build agreement matrix                              │
│     └─> Aggregate risks                                     │
├─────────────────────────────────────────────────────────────┤
│  8. [REFLECT] - Output                                      │
│     ├─> Generate markdown report                            │
│     └─> Save JSON to ./reports/{ticker}_{date}.json         │
└─────────────────────────────────────────────────────────────┘
```

---

## STEP 1: MODE SELECTION

### 1.1 Mode Detection

First, check if the user specified a mode flag:
- `--quick` or `--fast` → **Quick Mode**
- `--full` or `--deep` → **Full Mode**
- No flag → **Ask User**

### 1.2 Ask User (if no flag)

Use the AskUserQuestion tool:

```
question: "Quick lookup or Full analysis for {TICKER}?"
header: "Analysis Mode"
options:
  - label: "Quick lookup"
    description: "Key metrics and fundamentals only (~30 seconds)"
  - label: "Full analysis"
    description: "All 7 guru perspectives + consolidation (~3-5 minutes)"
```

### 1.3 Mode Comparison

| Aspect | Quick Mode | Full Mode |
|--------|------------|-----------|
| **Data Fetched** | Metrics, prices, company_facts | ALL data for all experts |
| **Expert Analyses** | None | All 7 gurus in parallel |
| **13-F Holdings** | None | 5 investors |
| **News/Search** | Basic context | Finance + news + risk searches |
| **Output** | Simple metrics table | Full report with all analyses |
| **Approximate Time** | 30 seconds | 3-5 minutes |

---

## STEP 2: DATA ROUTING LOGIC

### 2.1 Expert Data Requirements Matrix

Each expert needs specific data. Fetch the UNION once, then route SUBSETS to each expert.

```
┌─────────────────┬────┬────┬────┬────┬────┬────┬────┐
│ Data Type       │ WB │ BG │ PL │ CW │ GS │ RD │ MB │
├─────────────────┼────┼────┼────┼────┼────┼────┼────┤
│ income_statements│ ✓  │ ✓  │ ✓  │ ✓  │    │    │ ✓  │
│ balance_sheets  │ ✓  │ ✓  │ ✓  │ ✓  │    │ ✓  │ ✓  │
│ cash_flows      │ ✓  │ ✓  │ ✓  │ ✓  │    │ ✓  │ ✓  │
│ financial_metrics│ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │
│ company_facts   │ ✓  │    │ ✓  │ ✓  │    │    │ ✓  │
│ prices          │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │
│ insider_trades  │ ✓  │    │ ✓  │    │    │    │ ✓  │
│ sec_filings     │ ✓  │ ✓  │ ✓  │ ✓  │    │ ✓  │ ✓  │
│ 13f_berkshire   │ ✓  │    │    │    │    │    │    │
│ 13f_ark         │    │    │    │ ✓  │    │    │    │
│ 13f_soros       │    │    │    │    │ ✓  │    │    │
│ 13f_bridgewater │    │    │    │    │    │ ✓  │    │
│ 13f_scion       │    │    │    │    │    │    │ ✓  │
│ news_finance    │ ✓  │    │ ✓  │ ✓  │ ✓  │    │ ✓  │
│ news_recent     │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │
│ news_risks      │    │    │    │    │    │ ✓  │ ✓  │
│ news_risks      │    │    │    │    │    │ ✓  │ ✓  │ ✓  │
└─────────────────┴────┴────┴────┴────┴────┴────┴────┴────┘

Legend: WB=Buffett, BG=Graham, PL=Lynch, CW=Wood, GS=Soros, RD=Dalio, MB=Burry, CR=Risk Officer
```

### 2.2 Data Windows (Extended)

Extended data windows for full business cycle coverage:

| Data Type | Window | Rationale |
|-----------|--------|-----------|
| Income Statements (Annual) | **15 years** | Full business cycle + multiple recessions |
| Income Statements (Quarterly) | **20 quarters** | Seasonal patterns + recent trend analysis |
| Balance Sheets (Annual) | **15 years** | Long-term capital structure evolution |
| Cash Flow Statements (Annual) | **15 years** | Cash generation consistency |
| Price History | **5 years** | Medium-term technical context |
| 13-F Holdings | **3 years (12 quarters)** | Position building/reduction patterns |
| Insider Trades | **100 records** | Recent management sentiment |

### 2.3 Data Fetch Sequence (Full Mode)

Execute these MCP tool calls to gather the full data union:

```python
# ═══════════════════════════════════════════════════════════
# PHASE 1: Financial Data (financialdatasets-mcp)
# Extended windows for professional analysis
# ═══════════════════════════════════════════════════════════

# Financial Statements - fetch in parallel (extended windows)
get_income_statements(ticker="{TICKER}", period="annual", limit=15)      # 15 years
get_income_statements(ticker="{TICKER}", period="quarterly", limit=20)   # 20 quarters
get_balance_sheets(ticker="{TICKER}", period="annual", limit=15)         # 15 years
get_cash_flows(ticker="{TICKER}", period="annual", limit=15)             # 15 years

# Metrics & Market Data - fetch in parallel
get_financial_metrics(ticker="{TICKER}", period="ttm", limit=8)          # 8 TTM periods
get_company_facts(ticker="{TICKER}")
get_prices(ticker="{TICKER}", start_date="{FIVE_YEARS_AGO}", end_date="{TODAY}", interval="day")  # 5 years
get_insider_trades(ticker="{TICKER}", limit=100)                         # 100 records

# SEC Filings
get_sec_filings(ticker="{TICKER}", limit=20)

# ═══════════════════════════════════════════════════════════
# PHASE 2: 13-F Holdings (financialdatasets-mcp)
# Investor-first approach: Query each investor's full portfolio,
# then filter for target ticker. Also get all owners of ticker.
# ═══════════════════════════════════════════════════════════

# Calculate 3-year lookback date
report_period_gte = "{THREE_YEARS_AGO}"  # e.g., "2022-01-01"

# Step 1: Fetch each guru's full portfolio (investor-first)
get_institutional_ownership(
    investor="BERKSHIRE_HATHAWAY_INC",
    limit=500,
    report_period_gte=report_period_gte
)  # Buffett - large portfolio

get_institutional_ownership(
    investor="ARK_INVESTMENT_MANAGEMENT_LLC",
    limit=300,
    report_period_gte=report_period_gte
)  # Wood

get_institutional_ownership(
    investor="SOROS_FUND_MANAGEMENT_LLC",
    limit=300,
    report_period_gte=report_period_gte
)  # Soros

get_institutional_ownership(
    investor="BRIDGEWATER_ASSOCIATES_LP",
    limit=500,
    report_period_gte=report_period_gte
)  # Dalio - large portfolio

get_institutional_ownership(
    investor="SCION_ASSET_MANAGEMENT_LLC",
    limit=200,
    report_period_gte=report_period_gte
)  # Burry - concentrated portfolio

# Step 2: Get ALL institutional owners of target ticker
get_institutional_ownership(ticker="{TICKER}", limit=100)

# ═══════════════════════════════════════════════════════════
# PHASE 3: News & Context (tavily-mcp)
# ═══════════════════════════════════════════════════════════

# Finance-specific search
search_finance(query="{TICKER} stock analysis valuation", ticker="{TICKER}", max_results=10)

# Recent news
search_news(query="{TICKER} earnings revenue", ticker="{TICKER}", max_age_days=14, max_results=10)

# Risk-focused search
search_news(query="{TICKER} risks concerns problems", ticker="{TICKER}", max_age_days=30, max_results=10, use_trusted_domains=True)

```

---

## STEP 2B: PYTHON PROCESSING LAYER

After fetching raw data, run the Python processing layer to pre-calculate professional metrics.

### 2B.1 Processing Layer Location

```
/processing/
├── __init__.py              # Main exports
├── orchestrator.py          # Entry point: run_analysis()
├── data_extractor.py        # Maps API responses to Python objects
├── metrics_calculator.py    # All composite score calculations
└── financial_metrics.py     # Legacy calculations (backwards compat)
```

### 2B.2 Processing Layer Usage

```python
from processing import run_analysis, format_for_expert

# Run full analysis pipeline
result = run_analysis(
    ticker="{TICKER}",
    income_statements=income_statements_response,
    balance_sheets=balance_sheets_response,
    cash_flows=cash_flows_response,
    metrics=metrics_response,
    price_data=price_response,
    holdings_by_investor={
        "BERKSHIRE_HATHAWAY_INC": berkshire_holdings,
        "ARK_INVESTMENT_MANAGEMENT_LLC": ark_holdings,
        "SOROS_FUND_MANAGEMENT_LLC": soros_holdings,
        "BRIDGEWATER_ASSOCIATES_LP": bridgewater_holdings,
        "SCION_ASSET_MANAGEMENT_LLC": scion_holdings,
    },
    insider_trades=insider_trades_response,
    company_facts=company_facts_response,
    wacc=0.10,  # Default WACC for EVA calculation
)

# Get LLM-ready context
llm_context = result.to_llm_context()

# Get expert-specific context
buffett_context = format_for_expert(result, "buffett")
burry_context = format_for_expert(result, "burry")
```

### 2B.3 Metrics Calculated (NOT from API)

The processing layer calculates metrics that financialdatasets.ai does NOT provide:

| Category | Metrics | Primary Users |
|----------|---------|---------------|
| **Composite Scores** | | |
| Piotroski F-Score | 9-point financial strength (0-9) | Graham, Buffett, Dalio, Burry |
| Altman Z-Score | Bankruptcy prediction (zones) | Graham, Dalio, Burry |
| Ohlson O-Score | Bankruptcy probability (0-1) | Dalio, Burry |
| Beneish M-Score | Earnings manipulation (-2.22 threshold) | Burry |
| Magic Formula | Greenblatt ROIC + Earnings Yield | Buffett |
| **Quality Metrics** | | |
| Sloan Accrual Ratio | Earnings quality (-10% to +10% safe) | Burry |
| Gross Profitability | Novy-Marx GP/Assets | Wood |
| FCF Conversion | FCF/EBITDA (>80% healthy) | Buffett |
| **Value Creation** | | |
| Owner Earnings | Buffett's true cash to owners | Buffett |
| EVA | NOPAT - (IC × WACC) | Dalio |
| **Decomposition** | | |
| DuPont 5-Factor | ROE breakdown (tax, interest, margin, turnover, leverage) | All |
| **Growth** | | |
| Sustainable Growth Rate | ROE × Retention Ratio | Lynch, Wood |
| Trend Analysis | Accelerating/Decelerating patterns | Lynch, Wood |
| **Shareholder Returns** | | |
| Total Shareholder Yield | Dividend + Buyback + Debt Paydown | Buffett |

### 2B.4 Metrics FROM API (Don't Recalculate)

financialdatasets.ai already provides these 48+ metrics - use directly:

- **Valuation**: P/E, P/B, P/S, EV/EBITDA, EV/Revenue, PEG
- **Profitability**: ROE, ROA, ROIC, Gross Margin, Operating Margin, Net Margin
- **Liquidity**: Current Ratio, Quick Ratio, Cash Ratio
- **Leverage**: Debt/Equity, Debt/Assets, Interest Coverage
- **Efficiency**: Asset Turnover, Inventory Turnover, DSO
- **Growth**: Revenue Growth, EPS Growth, FCF Growth
- **Per Share**: EPS, Book Value, FCF, Dividends

### 2B.5 Processing Layer Output Structure

```python
@dataclass
class AnalysisResult:
    ticker: str
    company_name: str
    analysis_date: str

    # Complete extracted company data
    company_data: CompanyData

    # All calculated metrics
    comprehensive_analysis: ComprehensiveAnalysis

    # Quick reference summary
    summary: Dict[str, Any]

    # Data quality notes
    data_quality_notes: List[str]

    def to_llm_context(self) -> str:
        """Format all metrics as LLM-ready text context."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""

@dataclass
class ComprehensiveAnalysis:
    ticker: str

    # Composite Scores
    piotroski: MetricResult      # F-Score (0-9)
    altman_z: MetricResult       # Z-Score with zone
    ohlson_o: MetricResult       # O-Score probability
    beneish_m: MetricResult      # M-Score with flags
    magic_formula: MetricResult  # Combined rank

    # Quality Metrics
    sloan_accrual: MetricResult
    gross_profitability: MetricResult
    fcf_conversion: MetricResult

    # Shareholder Returns
    shareholder_yield: MetricResult

    # Value Creation
    eva: MetricResult
    owner_earnings: MetricResult

    # Decomposition
    dupont: MetricResult

    # Growth
    sustainable_growth: MetricResult
    revenue_trend: MetricResult
    earnings_trend: MetricResult

    # Summary
    red_flags: List[str]
    green_flags: List[str]
    overall_quality_score: float  # 0-100

@dataclass
class MetricResult:
    value: float
    interpretation: str
    components: Dict[str, Any]
    flags: List[str]
    data_quality: float  # 0-1
```

### 2B.6 Example LLM Context Output

```markdown
# Pre-Calculated Metrics for AAPL
Company: Apple Inc
Analysis Date: 2026-01-23

## Composite Scores
### Piotroski F-Score: 8/9
Interpretation: Very Strong - High quality, consider buying
Components: ROA+, CFO+, ΔROA+, Accruals+, ΔLeverage+, ΔLiquidity+, NoDilution+, ΔMargin+, ΔTurnover-

### Altman Z-Score: 4.52
Interpretation: Safe Zone - Low bankruptcy risk

### Beneish M-Score: -2.85
Interpretation: Unlikely Manipulator (M=-2.85)

## Quality Metrics
### Sloan Accrual Ratio: -3.2%
Interpretation: Safe Zone - Quality earnings backed by cash

### FCF Conversion: 95.2%
Interpretation: Healthy - Strong cash conversion

### Gross Profitability (GP/Assets): 38.5%
Interpretation: Excellent gross profitability

## Value Creation
### Owner Earnings: $98.5B
Per Share: $6.42
Interpretation: Owner earnings exceed net income - high quality

### Economic Value Added (EVA): $72.3B
Interpretation: Creating value: $72.3B above cost of capital

## Shareholder Returns
### Total Shareholder Yield: 4.8%
  - Dividend Yield: 0.5%
  - Buyback Yield: 4.1%
  - Debt Paydown Yield: 0.2%

## ROE Decomposition (DuPont 5-Factor)
ROE: 147.2%
  - Tax Burden: 0.84
  - Interest Burden: 0.99
  - EBIT Margin: 30.1%
  - Asset Turnover: 1.15
  - Leverage: 5.12x
Analysis: ROE driven by strong margins, efficient asset use, leverage

## Sustainable Growth
Sustainable Growth Rate: 143.2%
Interpretation: High sustainable growth - can grow rapidly internally

## ✓ GREEN FLAGS
- Very strong Piotroski F-Score (8/9)
- Safe Altman Z-Score zone
- Low manipulation risk (Beneish < -2.22)
- Excellent FCF conversion (>80%)
- Positive EVA - creating shareholder value

## Overall Quality Score: 87/100
```

### 2.3 Data Fetch Sequence (Quick Mode)

Minimal data for quick lookup:

```python
# Quick mode - only essential metrics
get_financial_metrics(ticker="{TICKER}", period="ttm", limit=1)
get_company_facts(ticker="{TICKER}")
get_prices(ticker="{TICKER}", start_date="{90_DAYS_AGO}", end_date="{TODAY}", interval="day")

# Optional context
search_finance(query="{TICKER} stock", ticker="{TICKER}", max_results=3)
```

### 2.5 Data Subset Routing

After fetching raw data and running Python processing, route pre-calculated metrics to each expert:

```javascript
// Pre-calculated metrics from Python processing layer
const calculated = {
  piotroski: calculate_piotroski(financials),           // F-Score (0-9)
  altman: calculate_altman_z(financials, market_data),  // Z-Score
  beneish: calculate_beneish_m(financials),             // M-Score
  owner_earnings: calculate_owner_earnings(financials), // Buffett method
  roic: calculate_roic(financials),                     // Return on Invested Capital
  graham: calculate_graham_valuation(financials, price), // Graham Number, NCAV
  valuation: calculate_valuation_metrics(financials, market_data), // PEG, EV/EBITDA, etc.
  growth: calculate_growth_analysis(financials)         // CAGR, trends
};

const dataSubsets = {
  warren_buffett: {
    // Pre-calculated metrics (primary)
    owner_earnings: calculated.owner_earnings,
    roic: calculated.roic,
    piotroski: calculated.piotroski,
    valuation: calculated.valuation,
    growth: calculated.growth,
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: [...news_finance, ...news_recent],
    holdings_json: berkshire_holdings.filter(h => h.ticker === ticker)
  },

  ben_graham: {
    // Pre-calculated metrics (primary)
    graham: calculated.graham,           // Graham Number, NCAV
    piotroski: calculated.piotroski,     // Quality screen
    altman: calculated.altman,           // Bankruptcy risk
    valuation: calculated.valuation,
    growth: calculated.growth,
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: news_recent
    // No 13-F for Graham (historical reference)
  },

  peter_lynch: {
    // Pre-calculated metrics (primary)
    valuation: calculated.valuation,     // PEG ratio is key
    growth: calculated.growth,           // Growth trajectory
    piotroski: calculated.piotroski,     // Quality check
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: [...news_finance, ...news_recent],
    insider_trades: insider_trades
    // No 13-F for Lynch (historical reference)
  },

  cathie_wood: {
    // Pre-calculated metrics (primary)
    growth: calculated.growth,           // Revenue CAGR critical
    valuation: calculated.valuation,
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: [...news_finance, ...news_recent],
    holdings_json: ark_holdings.filter(h => h.ticker === ticker)
  },

  george_soros: {
    // Pre-calculated metrics (primary)
    valuation: calculated.valuation,
    // Context data (Soros focuses on price action & sentiment)
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    price_history: prices,  // Full 5-year price history for reflexivity analysis
    filings_content: null,
    news_items: [...news_finance, ...news_recent],
    holdings_json: soros_holdings.filter(h => h.ticker === ticker)
  },

  ray_dalio: {
    // Pre-calculated metrics (primary)
    altman: calculated.altman,           // Z-Score for stress testing
    roic: calculated.roic,
    piotroski: calculated.piotroski,
    valuation: calculated.valuation,
    growth: calculated.growth,
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: [...news_recent, ...news_risks],
    holdings_json: bridgewater_holdings.filter(h => h.ticker === ticker)
  },

  michael_burry: {
    // Burry gets EVERYTHING - he's the forensic analyst
    // Pre-calculated metrics (primary - forensic focus)
    beneish: calculated.beneish,         // M-Score for manipulation detection
    piotroski: calculated.piotroski,     // F-Score quality check
    altman: calculated.altman,           // Z-Score bankruptcy risk
    owner_earnings: calculated.owner_earnings, // Cash flow quality
    valuation: calculated.valuation,
    growth: calculated.growth,
    // Context data (full access for forensic analysis)
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,  // Full filings for forensic analysis
    news_items: [...news_finance, ...news_recent, ...news_risks],
    insider_trades: insider_trades,  // Critical for Burry
    holdings_json: scion_holdings.filter(h => h.ticker === ticker)
  }
    insider_trades: insider_trades,  // Critical for Burry
    holdings_json: scion_holdings.filter(h => h.ticker === ticker)
  },

  chief_risk_officer: {
    // Pre-calculated metrics (primary - downside focus)
    interest_coverage: calculated.interest_coverage,
    leverage: calculated.leverage,
    refi_risk: calculated.refi_risk,
    stress_test: calculated.stress_test,
    altman: calculated.altman,
    // Context data
    current_price: latest_price,
    market_cap: company_facts.market_cap,
    filings_content: sec_filings,
    news_items: [...news_risks, ...news_finance]
  }
};

// Expert-to-Metric Mapping Summary:
// ┌─────────────┬───────────┬─────────┬──────────┬────────┬──────┬────────┬───────┬────────┬──────────┐
// │ Expert      │ Piotroski │ Altman  │ Beneish  │ Owner  │ ROIC │ Graham │ Val.  │ Growth │ Credit   │
// ├─────────────┼───────────┼─────────┼──────────┼────────┼──────┼────────┼───────┼────────┼──────────┤
// │ Buffett     │     ✓     │         │          │   ✓    │  ✓   │        │   ✓   │   ✓    │          │
// │ Graham      │     ✓     │    ✓    │          │        │      │   ✓    │   ✓   │   ✓    │          │
// │ Lynch       │     ✓     │         │          │        │      │        │   ✓   │   ✓    │          │
// │ Wood        │           │         │          │        │      │        │   ✓   │   ✓    │          │
// │ Soros       │           │         │          │        │      │        │   ✓   │        │          │
// │ Dalio       │     ✓     │    ✓    │          │        │  ✓   │        │   ✓   │   ✓    │          │
// │ Burry       │     ✓     │    ✓    │    ✓     │   ✓    │      │        │   ✓   │   ✓    │          │
// │ Risk Officer│     ✓     │    ✓    │          │        │      │        │       │        │    ✓     │
// └─────────────┴───────────┴─────────┴──────────┴────────┴──────┴────────┴───────┴────────┴──────────┘
```

---

## STEP 3: SUBAGENT DISPATCH SYSTEM

### 3.1 Dispatch Pattern

**CRITICAL:** Spawn ALL 8 experts in a SINGLE message with multiple Task tool calls for true parallelism.

```
Use Task tool with:
  subagent_type: "general-purpose"
  description: "{Guru Name} analysis of {TICKER}"
  prompt: [Constructed from expert template + injected data]
```

### 3.2 Expert Prompt Construction

For each expert, construct the prompt by:

1. Load the expert template from `experts/{guru_id}.md`
2. Replace template variables with pre-calculated data:
   - `{TICKER}` → actual ticker symbol
   - `{COMPANY_NAME}` → from company_facts
   - `{current_price}` → latest price
   - `{market_cap}` → formatted market cap

   **Pre-calculated Metrics (from Python processing layer):**
   - `{piotroski_json}` → Piotroski F-Score with component breakdown
   - `{altman_json}` → Altman Z-Score with zone classification
   - `{beneish_json}` → Beneish M-Score with red flags
   - `{owner_earnings_json}` → Owner Earnings calculation
   - `{roic_json}` → ROIC with interpretation
   - `{graham_json}` → Graham Number and NCAV
   - `{valuation_json}` → PEG, EV/EBITDA, FCF yield, etc.
   - `{growth_json}` → CAGR, trends, acceleration

   **Context Data:**
   - `{filings_content}` → formatted SEC filings
   - `{news_items}` → formatted news items
   - `{holdings_json}` → 13-F holdings for this guru (with 3-year history)

### 3.3 Parallel Dispatch Call

Execute this SINGLE message with 7 Task tool invocations:

```
// DISPATCH ALL 7 EXPERTS IN PARALLEL - SINGLE MESSAGE

Task({
  subagent_type: "general-purpose",
  description: "Warren Buffett analysis of {TICKER}",
  prompt: constructedBuffettPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Ben Graham analysis of {TICKER}",
  prompt: constructedGrahamPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Peter Lynch analysis of {TICKER}",
  prompt: constructedLynchPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Cathie Wood analysis of {TICKER}",
  prompt: constructedWoodPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "George Soros analysis of {TICKER}",
  prompt: constructedSorosPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Ray Dalio analysis of {TICKER}",
  prompt: constructedDalioPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Michael Burry analysis of {TICKER}",
  prompt: constructedBurryPrompt
})

Task({
  subagent_type: "general-purpose",
  description: "Chief Risk Officer analysis of {TICKER}",
  prompt: constructedRiskOfficerPrompt
})
```

### 3.4 Response Collection

After parallel dispatch:
1. Collect all 7 responses
2. Parse JSON from each expert's response
3. Validate schema compliance
4. Handle any failures gracefully (continue with N-1 experts)

---

## STEP 4: DRIVER WORKFLOW EXECUTION

### 4.1 [DISCOVER] Phase

**Output to user:**
```
═══════════════════════════════════════════════════════════
[DISCOVER] Starting analysis for {TICKER}
═══════════════════════════════════════════════════════════

[DISCOVER] Fetching financial statements (15 years)...
[DISCOVER] Fetching metrics and market data...
[DISCOVER] Fetching SEC filings...
[DISCOVER] Fetching 13-F institutional holdings (3 years)...
[DISCOVER] Fetching news and market context...
[DISCOVER] Data collection complete.

Data Summary:
- Financial Statements: {N} annual + {N} quarterly periods
- Metrics: {N} metrics available
- Price History: {N} days (5 years)
- SEC Filings: {N} filings
- 13-F Holdings: {N} relevant positions found
- News Articles: {N} items
```

**Actions:**
1. Execute data fetch sequence based on mode
2. Store all data in structured format
3. Log any missing data points
4. Calculate data quality score

### 4.2 [PROCESS] Phase ⭐ NEW

**Output to user:**
```
═══════════════════════════════════════════════════════════
[PROCESS] Calculating professional metrics
═══════════════════════════════════════════════════════════

[PROCESS] Running Python processing layer...
[PROCESS] Calculating composite scores:
         ├─ Piotroski F-Score: {X}/9 ({interpretation})
         ├─ Altman Z-Score: {X} ({zone})
         ├─ Beneish M-Score: {X} ({interpretation})
         └─ Ohlson O-Score: {X}% probability

[PROCESS] Calculating quality metrics:
         ├─ Sloan Accrual: {X}%
         ├─ FCF Conversion: {X}%
         └─ Gross Profitability: {X}%

[PROCESS] Value creation analysis:
         ├─ Owner Earnings: ${X}
         └─ EVA: ${X}

[PROCESS] Generating expert contexts...
[PROCESS] Pre-calculation complete.

Quality Summary:
- Overall Quality Score: {X}/100
- Red Flags: {N}
- Green Flags: {N}
```

**Actions:**
1. Call `run_analysis()` from processing layer
2. Extract composite scores and quality metrics
3. Identify red/green flags
4. Generate expert-specific contexts using `format_for_expert()`
5. Log any calculation warnings

**Python Code:**
```python
from processing import run_analysis, format_for_expert

# Run full processing pipeline
result = run_analysis(
    ticker=ticker,
    income_statements=income_statements,
    balance_sheets=balance_sheets,
    cash_flows=cash_flows,
    metrics=metrics,
    price_data=price_data,
    holdings_by_investor=holdings_by_investor,
    insider_trades=insider_trades,
    company_facts=company_facts,
)

# Extract key metrics for display
analysis = result.comprehensive_analysis
print(f"Piotroski F-Score: {analysis.piotroski.value}/9")
print(f"Altman Z-Score: {analysis.altman_z.value}")
print(f"Overall Quality: {analysis.overall_quality_score}/100")

# Generate expert contexts
expert_contexts = {
    "buffett": format_for_expert(result, "buffett"),
    "graham": format_for_expert(result, "graham"),
    "lynch": format_for_expert(result, "lynch"),
    "wood": format_for_expert(result, "wood"),
    "soros": format_for_expert(result, "soros"),
    "dalio": format_for_expert(result, "dalio"),
    "burry": format_for_expert(result, "burry"),
}
```

### 4.4 [REPRESENT] Phase

**Output to user:**
```
═══════════════════════════════════════════════════════════
[REPRESENT] Planning analysis approach
═══════════════════════════════════════════════════════════

[REPRESENT] Mode: {FULL|QUICK}
[REPRESENT] Company: {COMPANY_NAME} ({TICKER})
[REPRESENT] Market Cap: ${MARKET_CAP}
[REPRESENT] Current Price: ${CURRENT_PRICE}

Pre-Calculated Metrics Summary:
  ├─ Piotroski F-Score: {X}/9 ({interpretation})
  ├─ Altman Z-Score: {X} ({zone})
  ├─ Quality Score: {X}/100
  └─ Red Flags: {N} | Green Flags: {N}

Experts to dispatch:
  ├─ Warren Buffett  (moat, owner earnings, FCF conversion)
  ├─ Ben Graham      (margin of safety, Z-Score, NCAV)
  ├─ Peter Lynch     (PEG, sustainable growth, trends)
  ├─ Cathie Wood     (disruption, gross profitability)
  ├─ George Soros    (reflexivity, sentiment)
  ├─ Ray Dalio       (cycles, stress testing, EVA)
  └─ Michael Burry   (M-Score, accruals, forensics)

[REPRESENT] Expert contexts prepared from processing layer.
```

**Actions:**
1. Validate ticker and data availability
2. Use `format_for_expert()` to prepare expert-specific contexts
3. Build the expert prompts with pre-calculated metrics
4. Log the analysis plan

### 4.5 [IMPLEMENT] Phase (Full Mode Only)

**Output to user:**
```
═══════════════════════════════════════════════════════════
[IMPLEMENT] Dispatching expert analysts (parallel execution)
═══════════════════════════════════════════════════════════

[IMPLEMENT] → Spawning Warren Buffett analysis...
[IMPLEMENT] → Spawning Ben Graham analysis...
[IMPLEMENT] → Spawning Peter Lynch analysis...
[IMPLEMENT] → Spawning Cathie Wood analysis...
[IMPLEMENT] → Spawning George Soros analysis...
[IMPLEMENT] → Spawning Ray Dalio analysis...
[IMPLEMENT] → Spawning Michael Burry analysis...

[IMPLEMENT] All 7 experts dispatched. Awaiting results...
```

**Actions:**
1. Send single message with 7 parallel Task calls
2. Wait for all responses
3. Log progress as each completes

**Post-dispatch output:**
```
[IMPLEMENT] ✓ Warren Buffett complete (signal: {SIGNAL})
[IMPLEMENT] ✓ Ben Graham complete (signal: {SIGNAL})
[IMPLEMENT] ✓ Peter Lynch complete (signal: {SIGNAL})
[IMPLEMENT] ✓ Cathie Wood complete (signal: {SIGNAL})
[IMPLEMENT] ✓ George Soros complete (signal: {SIGNAL})
[IMPLEMENT] ✓ Ray Dalio complete (signal: {SIGNAL})
[IMPLEMENT] ✓ Michael Burry complete (signal: {SIGNAL})

[IMPLEMENT] All expert analyses received.
```

### 4.6 [VALIDATE] Phase

**Output to user:**
```
═══════════════════════════════════════════════════════════
[VALIDATE] Cross-checking expert outputs
═══════════════════════════════════════════════════════════

[VALIDATE] Checking JSON schema compliance... {N}/7 valid
[VALIDATE] Checking for missing required fields... OK
[VALIDATE] Identifying contradictory assumptions...

Assumption Check:
  - Growth rate assumptions: Range {X%} to {Y%}
  - Valuation method disagreements: {N} found
  - Risk assessment divergence: {HIGH|MEDIUM|LOW}

[VALIDATE] Consensus strength: {STRONG|MODERATE|WEAK|DIVIDED}
```

**Actions:**
1. Validate each expert's JSON output
2. Check for required fields
3. Identify contradictory assumptions
4. Flag if consensus is suspiciously uniform (potential groupthink)

### 4.7 [EVOLVE] Phase

**Output to user:**
```
═══════════════════════════════════════════════════════════
[EVOLVE] Consolidating insights
═══════════════════════════════════════════════════════════

[EVOLVE] Signal distribution:
         Bullish:  {N} experts ({X}%)
         Neutral:  {N} experts ({X}%)
         Bearish:  {N} experts ({X}%)

[EVOLVE] Computing confidence-weighted consensus...
[EVOLVE] Building agreement matrix...
[EVOLVE] Aggregating risk factors...
[EVOLVE] Extracting common themes...
[EVOLVE] Computing price target consensus...

[EVOLVE] Consolidation complete.
```

**Actions:**

#### Step 1: Tally Signals
```javascript
const signalTally = {
  bullish: experts.filter(e => e.signal === "bullish").length,
  neutral: experts.filter(e => e.signal === "neutral").length,
  bearish: experts.filter(e => e.signal === "bearish").length
};

const bullishExperts = experts.filter(e => e.signal === "bullish").map(e => e.expert);
const neutralExperts = experts.filter(e => e.signal === "neutral").map(e => e.expert);
const bearishExperts = experts.filter(e => e.signal === "bearish").map(e => e.expert);
```

#### Step 2: Compute Confidence-Weighted Signal
```javascript
// Weight each signal by confidence
const weightedScore = experts.reduce((sum, e) => {
  const signalValue = { bullish: 1, neutral: 0, bearish: -1 }[e.signal];
  return sum + (signalValue * e.confidence);
}, 0) / experts.reduce((sum, e) => sum + e.confidence, 0);

// Convert to 0-100 scale (50 = neutral)
const confidenceWeightedScore = Math.round((weightedScore + 1) * 50);

// Determine overall signal
const confidenceWeightedSignal =
  confidenceWeightedScore > 60 ? "bullish" :
  confidenceWeightedScore < 40 ? "bearish" : "neutral";
```

#### Step 3: Build Agreement Matrix
Track which experts mentioned which themes and whether positively or negatively.

```javascript
// Themes to track across experts
const TRACKED_THEMES = [
  "Strong moat / Competitive advantage",
  "Management quality",
  "Valuation attractive",
  "Growth potential",
  "Balance sheet strength",
  "Cash flow quality",
  "Accounting concerns",
  "Macro/cycle headwinds",
  "Disruption risk",
  "Insider activity signal"
];

// Build matrix: theme -> expert -> positive/negative/not_mentioned
const agreementMatrix = {};
for (const theme of TRACKED_THEMES) {
  agreementMatrix[theme] = {};
  for (const expert of experts) {
    // Analyze expert's thesis, analysis, and key_risks for theme mentions
    const sentiment = analyzeThemeSentiment(expert, theme);
    agreementMatrix[theme][expert.expert] = sentiment; // "positive", "negative", "not_mentioned"
  }
}

// Extract agreement themes (3+ experts positive on same theme)
const agreementThemes = TRACKED_THEMES.filter(theme =>
  Object.values(agreementMatrix[theme]).filter(s => s === "positive").length >= 3
).map(theme => ({
  theme,
  experts_agreeing: Object.entries(agreementMatrix[theme])
    .filter(([_, s]) => s === "positive")
    .map(([e, _]) => e),
  count: Object.values(agreementMatrix[theme]).filter(s => s === "positive").length
}));

// Extract divergence themes (some positive, some negative)
const divergenceThemes = TRACKED_THEMES.filter(theme => {
  const sentiments = Object.values(agreementMatrix[theme]);
  return sentiments.includes("positive") && sentiments.includes("negative");
}).map(theme => ({
  theme,
  bull_view: synthesizeBullView(experts, theme),
  bear_view: synthesizeBearView(experts, theme),
  experts_split: {
    bullish_on_theme: Object.entries(agreementMatrix[theme])
      .filter(([_, s]) => s === "positive").map(([e, _]) => e),
    bearish_on_theme: Object.entries(agreementMatrix[theme])
      .filter(([_, s]) => s === "negative").map(([e, _]) => e)
  }
}));
```

#### Step 4: Aggregate Risks
Union all `key_risks` arrays, deduplicate similar risks, track attribution.

```javascript
// Collect all risks with attribution
const allRisksRaw = experts.flatMap(e =>
  e.key_risks.map(risk => ({ risk, expert: e.expert }))
);

// Deduplicate similar risks (fuzzy matching on key terms)
const allRisks = deduplicateRisks(allRisksRaw);

// Sort by number of experts flagging (severity proxy)
allRisks.sort((a, b) => b.flagged_by.length - a.flagged_by.length);

// Assign severity based on expert count
allRisks.forEach(r => {
  r.severity = r.flagged_by.length >= 4 ? "high" :
               r.flagged_by.length >= 2 ? "medium" : "low";
});

function deduplicateRisks(risks) {
  const deduplicated = [];
  for (const { risk, expert } of risks) {
    // Check if similar risk already exists
    const existing = deduplicated.find(r =>
      similarityScore(r.risk, risk) > 0.7  // 70% similarity threshold
    );
    if (existing) {
      if (!existing.flagged_by.includes(expert)) {
        existing.flagged_by.push(expert);
      }
    } else {
      deduplicated.push({ risk, flagged_by: [expert] });
    }
  }
  return deduplicated;
}
```

#### Step 5: Compute Price Target Consensus
```javascript
// Parse price targets from experts
const priceTargets = experts.map(e => ({
  expert: e.expert,
  buy_at: parsePriceString(e.would_buy_at),
  target: parsePriceFromOutlook(e.forward_outlook.price_target),
  sell_at: parsePriceString(e.would_sell_at)
})).filter(p => p.target !== null);

// Calculate consensus (median to avoid outlier skew)
const consensusPriceTargets = {
  consensus_buy_below: median(priceTargets.map(p => p.buy_at).filter(Boolean)),
  consensus_target: median(priceTargets.map(p => p.target).filter(Boolean)),
  consensus_sell_above: median(priceTargets.map(p => p.sell_at).filter(Boolean)),
  range_low: Math.min(...priceTargets.map(p => p.target).filter(Boolean)),
  range_high: Math.max(...priceTargets.map(p => p.target).filter(Boolean))
};
```

#### Step 6: Synthesize Bull and Bear Cases
```javascript
// Bull case: Synthesize from bullish experts
const bullCaseSummary = bullishExperts.length > 0 ?
  synthesizeCaseFromExperts(
    experts.filter(e => bullishExperts.includes(e.expert)),
    "bullish"
  ) : "No experts are currently bullish on this stock.";

// Bear case: Synthesize from bearish experts
const bearCaseSummary = bearishExperts.length > 0 ?
  synthesizeCaseFromExperts(
    experts.filter(e => bearishExperts.includes(e.expert)),
    "bearish"
  ) : "No experts are currently bearish on this stock.";

// Neutral case (if any)
const neutralCaseSummary = neutralExperts.length > 0 ?
  synthesizeCaseFromExperts(
    experts.filter(e => neutralExperts.includes(e.expert)),
    "neutral"
  ) : "No experts are currently neutral on this stock.";
```

#### Step 7: Final Consolidation Object
```javascript
const consolidation = {
  signal_tally: signalTally,
  confidence_weighted_signal: confidenceWeightedSignal,
  confidence_weighted_score: confidenceWeightedScore,
  agreement_themes: agreementThemes,
  divergence_themes: divergenceThemes,
  all_risks: allRisks,
  bull_case_summary: bullCaseSummary,
  bear_case_summary: bearCaseSummary,
  neutral_case_summary: neutralCaseSummary,
  price_targets: consensusPriceTargets,
  agreement_matrix: agreementMatrix
};
```

### 4.8 [REFLECT] Phase

**Output to user:**
```
═══════════════════════════════════════════════════════════
[REFLECT] Generating final report
═══════════════════════════════════════════════════════════

[REFLECT] Formatting markdown report...
[REFLECT] Populating executive summary...
[REFLECT] Formatting 7 expert analyses...
[REFLECT] Building agreement matrix visualization...
[REFLECT] Saving JSON to ./reports/{TICKER}_{DATE}.json
[REFLECT] Analysis complete.

═══════════════════════════════════════════════════════════
```

**Actions:**

#### Step 1: Format Expert Signal Table
```javascript
const expertSignalTable = experts.map(e => {
  const signalEmoji = { bullish: "🟢", neutral: "🟡", bearish: "🔴" }[e.signal];
  const keyInsight = extractKeyInsight(e.thesis, 50); // First 50 chars of key insight
  return `| ${formatExpertName(e.expert)} | ${signalEmoji} ${e.signal} | ${e.confidence}% | ${keyInsight} |`;
}).join("\n");

// Sort by confidence for display
experts.sort((a, b) => b.confidence - a.confidence);
```

#### Step 2: Format Agreement Matrix Visualization
```javascript
// ASCII matrix for markdown display
const matrixHeaders = ["Theme", "WB", "BG", "PL", "CW", "GS", "RD", "MB"];
const matrixDivider = "|" + matrixHeaders.map(h => "---").join("|") + "|";

const matrixRows = Object.entries(agreementMatrix).map(([theme, experts]) => {
  const cells = ["WB", "BG", "PL", "CW", "GS", "RD", "MB"].map(abbrev => {
    const expertId = abbreviationToExpertId(abbrev);
    const sentiment = experts[expertId];
    return sentiment === "positive" ? "✓" :
           sentiment === "negative" ? "✗" : "·";
  });
  return `| ${theme} | ${cells.join(" | ")} |`;
}).join("\n");
```

#### Step 3: Format Price Target Table
```javascript
const priceTargetTable = experts.map(e => {
  const buy = e.would_buy_at || "N/A";
  const target = e.forward_outlook.price_target || "N/A";
  const sell = e.would_sell_at || "N/A";
  return `| ${formatExpertName(e.expert)} | ${buy} | ${target} | ${sell} |`;
}).join("\n");
```

#### Step 4: Generate Signal Distribution Bar
```javascript
function generateSignalBar(count, total, char = "█") {
  const barLength = Math.round((count / total) * 20);
  return char.repeat(barLength);
}

const bullishBar = generateSignalBar(signalTally.bullish, 7);
const neutralBar = generateSignalBar(signalTally.neutral, 7);
const bearishBar = generateSignalBar(signalTally.bearish, 7);
```

#### Step 5: Format Each Expert Section
For each expert, format using this structure:

```markdown
### {Expert Display Name}

**Signal:** {emoji} {signal} | **Confidence:** {confidence}%

> **Thesis:** {thesis}

#### Forward Outlook

| Aspect | Assessment |
|--------|------------|
| **Prediction** | {prediction} |
| **Timeline** | {timeline} |
| **Price Target** | {price_target} |
| **Catalyst** | {catalyst} |

#### Analysis Breakdown

{For each criterion in expert.analysis:}
**{Criterion Name}:** {summary with key data points}
- Score: {score}/10
- Key finding: {most important reasoning point}

#### Risk Assessment

**Key Risks Identified:**
1. {risk1}
2. {risk2}
3. {risk3}

**What Would Change This View:**
- {change1}
- {change2}

#### Holdings Context

| Metric | Value |
|--------|-------|
| **Current Position** | {current_position} |
| **Recent Changes** | {recent_changes} |
| **Signal from Actions** | {signal_from_actions} |

#### Entry/Exit Levels

- **Would buy aggressively at:** {would_buy_at}
- **Would start selling at:** {would_sell_at}

#### Private Assessment

> *{private_assessment}*
```

#### Step 6: Assemble Final Report
Use the template from `templates/consolidated_report_template.md` and replace all placeholders:

```javascript
const finalReport = reportTemplate
  .replace("{TICKER}", ticker)
  .replace("{DATE}", formatDate(new Date()))
  .replace("{MODE}", "Full")
  .replace("{VERSION}", "1.0.0")
  .replace("{BULLISH_COUNT}", signalTally.bullish)
  .replace("{NEUTRAL_COUNT}", signalTally.neutral)
  .replace("{BEARISH_COUNT}", signalTally.bearish)
  .replace("{WEIGHTED_SIGNAL}", confidenceWeightedSignal)
  .replace("{WEIGHTED_SCORE}", confidenceWeightedScore)
  .replace("{AGREEMENT_SUMMARY}", agreementThemes[0]?.theme || "No strong agreement")
  .replace("{DIVERGENCE_SUMMARY}", divergenceThemes[0]?.theme || "No major divergence")
  .replace("{CURRENT_PRICE}", currentPrice)
  .replace("{CONSENSUS_TARGET}", consensusPriceTargets.consensus_target)
  .replace("{BULL_CASE_SUMMARY}", bullCaseSummary)
  .replace("{BEAR_CASE_SUMMARY}", bearCaseSummary)
  .replace("{NEUTRAL_CASE_SUMMARY}", neutralCaseSummary)
  .replace("{BULLISH_EXPERTS}", bullishExperts.map(formatExpertName).join(", "))
  .replace("{BEARISH_EXPERTS}", bearishExperts.map(formatExpertName).join(", "))
  .replace("{NEUTRAL_EXPERTS}", neutralExperts.map(formatExpertName).join(", "))
  .replace("{EXPERT_SIGNAL_TABLE}", expertSignalTable)
  .replace("{AGREEMENT_MATRIX_ROWS}", matrixRows)
  .replace("{PRICE_TARGET_TABLE}", priceTargetTable)
  // ... etc for all placeholders
  ;
```

#### Step 7: Save JSON Output
```javascript
// Construct full JSON report
const jsonReport = {
  meta: {
    ticker: ticker,
    company_name: companyName,
    generated_at: new Date().toISOString(),
    mode: "full",
    skill_version: "1.0.0",
    current_price: currentPrice,
    market_cap: marketCap
  },
  data_sources: {
    financial_data: { source: "financialdatasets.ai", retrieved_at: dataFetchTime },
    news: { source: "tavily", max_age_days: 14, article_count: newsCount },
    sec_filings: secFilingsSummary,
    thirteenf_holdings: holdingsSummary
  },
  experts: {
    warren_buffett: expertOutputs.warren_buffett,
    ben_graham: expertOutputs.ben_graham,
    peter_lynch: expertOutputs.peter_lynch,
    cathie_wood: expertOutputs.cathie_wood,
    george_soros: expertOutputs.george_soros,
    ray_dalio: expertOutputs.ray_dalio,
    michael_burry: expertOutputs.michael_burry
  },
  consolidation: consolidation,
  quick_metrics: quickMetrics
};

// Save to file
const reportPath = `./reports/${ticker}_${formatDateForFilename(new Date())}.json`;
// Use Write tool to save the JSON file
```

#### Step 8: Display Report to User
Output the formatted markdown report directly to the user. The report should:
1. Start with the executive summary
2. Show signal distribution visually
3. Include all 7 expert analyses in full
4. End with consolidation, risks, and methodology notes

---

## STEP 5: OUTPUT GENERATION

### 5.1 Quick Mode Output

Quick mode still runs the Python processing layer but skips expert dispatch.

```markdown
# {TICKER} Quick Lookup

**{COMPANY_NAME}** | ${CURRENT_PRICE} | Market Cap: ${MARKET_CAP}

## Composite Scores (Pre-Calculated)

| Score | Value | Interpretation |
|-------|-------|----------------|
| **Piotroski F-Score** | {X}/9 | {interpretation} |
| **Altman Z-Score** | {X} | {zone} |
| **Beneish M-Score** | {X} | {manipulation_risk} |
| **Overall Quality** | {X}/100 | {quality_interpretation} |

## Key Metrics (from API)

| Metric | Value | Assessment |
|--------|-------|------------|
| P/E Ratio | {PE} | {vs_sector} |
| P/B Ratio | {PB} | |
| PEG Ratio | {PEG} | |
| ROE | {ROE}% | |
| ROIC | {ROIC}% | |
| Debt/Equity | {DE} | |
| Revenue Growth | {RG}% | YoY |
| FCF Conversion | {FCF_CONV}% | |
| Free Cash Flow | ${FCF} | |

## Quality Indicators

### Green Flags ✓
{list of green_flags from processing layer}

### Red Flags ⚠️
{list of red_flags from processing layer}

## Price Context

- **Current:** ${CURRENT_PRICE}
- **52-week Range:** ${LOW} - ${HIGH}
- **Distance from High:** {X}%

## Quick Assessment

{2-3 sentence summary based on composite scores and flags}

---
*Quick lookup generated by financial-researcher v2.0.0*
*Processing layer: Piotroski, Altman, Beneish, Quality Score*
*For full 7-guru analysis, run with --full flag*
```

### 5.2 Full Mode Output

Use the template from `templates/consolidated_report_template.md`

Key sections:
1. Executive Summary with signal tally
2. Each of 7 expert analyses IN FULL
3. Consolidation with agreement matrix
4. All risks aggregated
5. Price target summary
6. Data sources and methodology

### 5.3 JSON Output Structure

Save to `./reports/{TICKER}_{YYYY-MM-DD}.json`:

```json
{
  "meta": {
    "ticker": "{TICKER}",
    "company_name": "{COMPANY_NAME}",
    "generated_at": "{ISO_DATETIME}",
    "mode": "full",
    "skill_version": "2.0.0",
    "processing_version": "2.0.0",
    "current_price": {PRICE},
    "market_cap": {MARKET_CAP}
  },
  "data_sources": {
    "financial_data": {
      "source": "financialdatasets.ai",
      "retrieved_at": "{ISO_DATETIME}",
      "periods_annual": 15,
      "periods_quarterly": 20
    },
    "news": {
      "source": "tavily",
      "max_age_days": 14,
      "article_count": {N}
    },
    "sec_filings": [
      {"type": "10-K", "period": "2025", "items_extracted": ["1", "1A", "7"]}
    ],
    "thirteenf_holdings": {
      "berkshire_hathaway": {"as_of_date": "2025-09-30", "has_position": true},
      "ark_invest": {"as_of_date": "2025-12-31", "has_position": false}
    }
  },
  "processing_layer": {
    "composite_scores": {
      "piotroski_f_score": {
        "value": 8,
        "max": 9,
        "interpretation": "Very Strong - High quality",
        "components": {
          "f1_roa_positive": 1,
          "f2_cfo_positive": 1,
          "f3_roa_improving": 1,
          "f4_accruals_quality": 1,
          "f5_leverage_decreasing": 1,
          "f6_liquidity_improving": 1,
          "f7_no_dilution": 1,
          "f8_margin_improving": 1,
          "f9_turnover_improving": 0
        }
      },
      "altman_z_score": {
        "value": 4.52,
        "zone": "safe",
        "interpretation": "Safe Zone - Low bankruptcy risk",
        "components": {
          "x1_working_capital_ratio": 0.15,
          "x2_retained_earnings_ratio": 0.45,
          "x3_ebit_ratio": 0.22,
          "x4_market_to_liabilities": 2.8,
          "x5_asset_turnover": 1.1
        }
      },
      "ohlson_o_score": {
        "value": 0.02,
        "probability_percent": 2.0,
        "interpretation": "Lower bankruptcy risk (2%)"
      },
      "beneish_m_score": {
        "value": -2.85,
        "likely_manipulator": false,
        "interpretation": "Unlikely Manipulator",
        "red_flags": []
      },
      "magic_formula": {
        "combined_score": 45.2,
        "earnings_yield": 6.5,
        "roic": 38.7
      }
    },
    "quality_metrics": {
      "sloan_accrual_ratio": {
        "value": -3.2,
        "interpretation": "Safe Zone - Quality earnings backed by cash"
      },
      "gross_profitability": {
        "value": 38.5,
        "interpretation": "Excellent gross profitability"
      },
      "fcf_conversion": {
        "value": 95.2,
        "interpretation": "Healthy - Strong cash conversion"
      }
    },
    "value_creation": {
      "owner_earnings": {
        "value": 98500000000,
        "per_share": 6.42,
        "interpretation": "Owner earnings exceed net income - high quality"
      },
      "eva": {
        "value": 72300000000,
        "interpretation": "Creating value: $72.3B above cost of capital"
      }
    },
    "shareholder_returns": {
      "total_yield": 4.8,
      "dividend_yield": 0.5,
      "buyback_yield": 4.1,
      "debt_paydown_yield": 0.2
    },
    "dupont_analysis": {
      "roe": 147.2,
      "tax_burden": 0.84,
      "interest_burden": 0.99,
      "ebit_margin": 30.1,
      "asset_turnover": 1.15,
      "leverage": 5.12
    },
    "growth": {
      "sustainable_growth_rate": 143.2,
      "revenue_trend": "accelerating",
      "earnings_trend": "stable"
    },
    "summary": {
      "overall_quality_score": 87,
      "red_flags": [],
      "green_flags": [
        "Very strong Piotroski F-Score (8/9)",
        "Safe Altman Z-Score zone",
        "Low manipulation risk",
        "Excellent FCF conversion"
      ]
    }
  },
  "experts": {
    "warren_buffett": { /* complete expert output JSON */ },
    "ben_graham": { /* complete expert output JSON */ },
    "peter_lynch": { /* complete expert output JSON */ },
    "cathie_wood": { /* complete expert output JSON */ },
    "george_soros": { /* complete expert output JSON */ },
    "ray_dalio": { /* complete expert output JSON */ },
    "michael_burry": { /* complete expert output JSON */ }
  },
  "consolidation": {
    "signal_tally": {"bullish": 4, "neutral": 2, "bearish": 1},
    "confidence_weighted_signal": "bullish",
    "confidence_weighted_score": 67,
    "agreement_themes": [
      {"theme": "Strong moat", "experts_agreeing": ["warren_buffett", "peter_lynch"], "count": 2}
    ],
    "divergence_themes": [
      {"theme": "Valuation", "bull_view": "...", "bear_view": "...", "experts_split": {...}}
    ],
    "all_risks": [
      {"risk": "China revenue exposure", "flagged_by": ["ray_dalio", "michael_burry"], "severity": "high"}
    ],
    "bull_case_summary": "...",
    "bear_case_summary": "...",
    "price_targets": {
      "consensus_buy_below": 150,
      "consensus_target": 195,
      "consensus_sell_above": 240,
      "range_low": 120,
      "range_high": 280
    }
  },
  "api_metrics": {
    "pe_ratio": 25.4,
    "pb_ratio": 8.2,
    "peg_ratio": 1.8,
    "roe": 42.1,
    "roic": 38.7,
    "debt_to_equity": 0.45,
    "current_ratio": 1.2,
    "revenue_growth": 8.5,
    "eps_growth": 12.3
  }
}
```

---

## STEP 6: ERROR HANDLING

### 6.1 MCP Server Unavailable

```
[DISCOVER] ⚠️ financialdatasets-mcp not responding
[DISCOVER] Attempting WebFetch fallback...
```

**Fallback:** Use WebFetch to call API directly:
```
URL: https://api.financialdatasets.ai/{endpoint}
Headers: X-API-KEY: {from environment}
```

### 6.2 Expert Subagent Failure

```
[IMPLEMENT] ⚠️ {Guru Name} analysis failed: {error_message}
[IMPLEMENT] Continuing with remaining {N} experts...
```

**Actions:**
1. Log the error
2. Continue with remaining experts
3. Note missing expert in final output
4. Adjust consolidation to work with available data

### 6.3 Missing Data

```
[DISCOVER] ⚠️ 13-F data not available for SCION_ASSET_MANAGEMENT_LLC
[DISCOVER] Michael Burry will analyze without holdings context
```

**Actions:**
1. Pass null/empty for missing data
2. Experts should handle gracefully and note in their analysis
3. Adjust confidence accordingly

### 6.4 Invalid Ticker

```
[DISCOVER] ❌ Ticker "{X}" not found
[DISCOVER] Suggestions: Did you mean {SIMILAR_TICKER}?
```

**Actions:**
1. Inform user
2. Suggest similar tickers if possible
3. Ask user to confirm or provide correct ticker

### 6.5 Rate Limits

```
[DISCOVER] ⚠️ API rate limit reached for financialdatasets.ai
[DISCOVER] Waiting 60 seconds before retry...
```

**Actions:**
1. Implement exponential backoff
2. Inform user of delay
3. Continue when rate limit resets

---

## THE 7 GURUS

### Value Investors
| Guru | Focus | Key Criteria | 13-F Source |
|------|-------|--------------|-------------|
| **Warren Buffett** | Moat, intrinsic value, owner earnings | Circle of competence, moat durability, margin of safety | BERKSHIRE_HATHAWAY_INC |
| **Ben Graham** | Margin of safety, asset values | 7 defensive screens, NCAV, EPV | Historical reference |

### Growth Investors
| Guru | Focus | Key Criteria | 13-F Source |
|------|-------|--------------|-------------|
| **Peter Lynch** | GARP, business story | PEG ratio, stock classification, tenbagger potential | Historical reference |
| **Cathie Wood** | Disruption, TAM expansion | Wright's Law, 5-year model, innovation platforms | ARK_INVESTMENT_MANAGEMENT_LLC |

### Macro/Cycles
| Guru | Focus | Key Criteria | 13-F Source |
|------|-------|--------------|-------------|
| **George Soros** | Reflexivity, sentiment | Boom-bust stage, narrative momentum, feedback loops | SOROS_FUND_MANAGEMENT_LLC |
| **Ray Dalio** | Debt cycles, history | Cycle position, stress tests, historical templates | BRIDGEWATER_ASSOCIATES_LP |

### Contrarian/Risk
| Guru | Focus | Key Criteria | 13-F Source |
|------|-------|--------------|-------------|
| **Michael Burry** | Forensics, bear case | Revenue/earnings quality, hidden liabilities, contrarian signals | SCION_ASSET_MANAGEMENT_LLC |

---

## KEY PRINCIPLES (NEVER DEVIATE)

1. **Independent Analyses**: Each guru forms their OWN thesis. No debate between them.

2. **All Preserved**: Consolidation ADDS synthesis, never REMOVES individual insights.

3. **Bold Forward-Looking**: Internal use only. Specific predictions, price targets, timelines.

4. **Changes > Holdings**: For 13-F data, recent changes matter more than static positions.

5. **Visible DRIVER**: Show all stage markers so user sees the methodology in action.

6. **Parallel Dispatch**: ALL 7 experts spawn in single message for true parallelism.

7. **Expert-Driven Data**: Each guru gets exactly what they need, fetched once as union.

8. **Quality Over Speed**: Flag missing data, don't hallucinate to fill gaps.

9. **Graceful Degradation**: If some experts fail, continue with available data.

10. **Complete Output**: Both markdown (displayed) and JSON (saved) for every analysis.

11. **Pre-Calculate, Don't Duplicate**: Use Python processing layer for composite scores. Don't recalculate what financialdatasets.ai provides.

12. **Processing Layer First**: ALWAYS run `run_analysis()` before expert dispatch. Experts receive pre-calculated metrics, not raw data.

---

## END-TO-END TEST PROCEDURE

### Test Command

```
/financial-researcher AAPL --full
```

### Expected Flow

1. **Mode Selection**: Should detect `--full` flag and skip mode question

2. **[DISCOVER] Phase** (10-30 seconds):
   - Fetch financial statements (15 years annual, 20 quarters)
   - Fetch metrics and market data
   - Fetch SEC filings
   - Fetch 13-F holdings for 5 investors (3-year history)
   - Fetch news and context from Tavily

   **Expected output:**
   ```
   [DISCOVER] Fetching financial statements (15 years)...
   [DISCOVER] Fetching metrics and market data...
   [DISCOVER] Fetching SEC filings...
   [DISCOVER] Fetching 13-F institutional holdings (3 years)...
   [DISCOVER] Fetching news and market context...
   [DISCOVER] Data collection complete.

   Data Summary:
   - Financial Statements: 15 annual + 20 quarterly periods
   - Metrics: 48+ metrics available
   - Price History: 1250+ days (5 years)
   - SEC Filings: 20+ filings
   - 13-F Holdings: X relevant positions found
   - News Articles: 20+ items
   ```

3. **[PROCESS] Phase** (2-5 seconds):
   - Run Python processing layer
   - Calculate composite scores
   - Generate expert contexts

   **Expected output:**
   ```
   [PROCESS] Running Python processing layer...
   [PROCESS] Calculating composite scores:
            ├─ Piotroski F-Score: 8/9 (Very Strong)
            ├─ Altman Z-Score: 4.52 (Safe Zone)
            ├─ Beneish M-Score: -2.85 (Unlikely Manipulator)
            └─ Ohlson O-Score: 2% probability

   [PROCESS] Calculating quality metrics:
            ├─ Sloan Accrual: -3.2%
            ├─ FCF Conversion: 95.2%
            └─ Gross Profitability: 38.5%

   [PROCESS] Value creation analysis:
            ├─ Owner Earnings: $98.5B
            └─ EVA: $72.3B

   Quality Summary:
   - Overall Quality Score: 87/100
   - Red Flags: 0
   - Green Flags: 4
   ```

4. **[REPRESENT] Phase** (1-2 seconds):
   - Validate ticker
   - Prepare data subsets with pre-calculated metrics
   - Build expert prompts using format_for_expert()

   **Expected output:**
   ```
   [REPRESENT] Mode: FULL
   [REPRESENT] Company: Apple Inc (AAPL)
   [REPRESENT] Market Cap: $X trillion
   [REPRESENT] Current Price: $XXX.XX

   Pre-Calculated Metrics Summary:
     ├─ Piotroski F-Score: 8/9 (Very Strong)
     ├─ Altman Z-Score: 4.52 (Safe Zone)
     ├─ Quality Score: 87/100
     └─ Red Flags: 0 | Green Flags: 4

   Experts to dispatch:
     ├─ Warren Buffett  (moat, owner earnings, FCF conversion)
     ├─ Ben Graham      (margin of safety, Z-Score, NCAV)
     ...
   ```

6. **[IMPLEMENT] Phase** (60-180 seconds):
   - Spawn 7 Task subagents in parallel
   - Each expert receives pre-calculated metrics from processing layer
   - Wait for all to complete

   **Expected output:**
   ```
   [IMPLEMENT] → Spawning Warren Buffett analysis...
   [IMPLEMENT] → Spawning Ben Graham analysis...
   ...
   [IMPLEMENT] All 7 experts dispatched. Awaiting results...

   [IMPLEMENT] ✓ Warren Buffett complete (signal: bullish)
   [IMPLEMENT] ✓ Ben Graham complete (signal: neutral)
   ...
   ```

7. **[VALIDATE] Phase** (2-5 seconds):
   - Check JSON schema compliance
   - Identify contradictions

   **Expected output:**
   ```
   [VALIDATE] Checking JSON schema compliance... 7/7 valid
   [VALIDATE] Checking for missing required fields... OK
   [VALIDATE] Consensus strength: MODERATE
   ```

8. **[EVOLVE] Phase** (5-10 seconds):
   - Tally signals
   - Build agreement matrix
   - Aggregate risks

   **Expected output:**
   ```
   [EVOLVE] Signal distribution:
            Bullish:  X experts (XX%)
            Neutral:  X experts (XX%)
            Bearish:  X experts (XX%)

   [EVOLVE] Consolidation complete.
   ```

9. **[REFLECT] Phase** (5-10 seconds):
   - Generate markdown report
   - Save JSON file (includes processing_layer section)
   - Display to user

### Validation Checklist

After test completes, verify:

**Processing Layer:**
- [ ] **Piotroski F-Score calculated** (0-9, with component breakdown)
- [ ] **Altman Z-Score calculated** (with zone: safe/grey/distress)
- [ ] **Beneish M-Score calculated** (with manipulation flags)
- [ ] **Overall Quality Score calculated** (0-100)
- [ ] **Red/Green flags identified** (not empty for AAPL)
- [ ] **Owner Earnings calculated** (Buffett method)
- [ ] **DuPont 5-factor breakdown** (ROE components)

**Expert Outputs:**
- [ ] **All 7 experts returned valid JSON**
- [ ] **Each expert has unique signal/confidence** (not identical outputs)
- [ ] **Experts reference pre-calculated metrics** (F-Score, Z-Score mentioned)
- [ ] **Thesis text is substantial** (3-5 sentences, not generic)
- [ ] **Forward outlook has specific predictions** (prices, timelines, catalysts)
- [ ] **Holdings context reflects actual 13-F data** (Berkshire owns AAPL)
- [ ] **Risks are specific to AAPL** (not generic "market risk")
- [ ] **Agreement matrix shows variation** (some ✓, some ✗, some ·)
- [ ] **Price targets vary by expert** (different philosophies = different targets)

**Output Files:**
- [ ] **JSON file saved to ./reports/AAPL_{date}.json**
- [ ] **JSON includes `processing_layer` section**
- [ ] **JSON file matches full_report_schema.json**

### Known AAPL Facts for Validation

Use these to verify expert analyses are using real data:

| Fact | Expected in Analysis |
|------|---------------------|
| **Berkshire ownership** | Buffett should mention ~5-6% of Berkshire's portfolio |
| **~$100B+ cash** | Graham/Dalio should note fortress balance sheet |
| **Services growth** | Lynch/Wood should discuss recurring revenue shift |
| **China exposure** | Burry/Dalio should flag as risk |
| **Buybacks** | Buffett should mention capital allocation |
| **Moat** | Buffett should rate ecosystem moat highly |
| **P/E ratio** | Graham should compare to historical averages |

### Test Failure Modes

If test fails, check:

1. **MCP servers not running**: Ensure both financialdatasets-mcp and tavily-mcp are configured
2. **API keys missing**: Check .env for FINANCIAL_DATASETS_API_KEY and TAVILY_API_KEY
3. **Expert timeout**: Increase Task tool timeout or check for infinite loops
4. **JSON parse error**: Expert returned malformed JSON - check expert prompt
5. **Missing holdings data**: 13-F data may not be available for current quarter

### Performance Benchmarks

| Phase | Target Time | Notes |
|-------|-------------|-------|
| DISCOVER | < 30s | Parallel MCP calls |
| PROCESS | < 5s | Python processing layer |
| REPRESENT | < 2s | Data routing only |
| IMPLEMENT | < 180s | Parallel expert dispatch |
| VALIDATE | < 5s | Schema validation |
| EVOLVE | < 10s | Consolidation logic |
| REFLECT | < 10s | Report generation |
| **Total** | **< 4 min** | Full mode target |

### Processing Layer Test

Run standalone processing layer test:

```bash
cd /mnt/d/github/FAskills/financial-researcher
python3 -m processing.test_pipeline
```

Expected output:
- All individual metric tests pass
- Full pipeline test passes
- Piotroski F-Score: 7/9 (test data)
- Altman Z-Score: 7.79 (test data)
- All calculations complete without errors
