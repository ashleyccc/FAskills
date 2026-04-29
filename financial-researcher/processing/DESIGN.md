# Python Processing Layer Design

## Overview

This module pre-calculates professional financial metrics from raw API data before passing to LLM experts. This approach:

1. **Reduces token usage** - Pre-computed metrics vs. raw financial statements
2. **Ensures accuracy** - Standard formulas applied consistently
3. **Enables validation** - Calculations can be verified independently
4. **Follows industry standards** - Uses established professional methodologies

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ financialdatasets.ai API                                        │
├─────────────────────────────────────────────────────────────────┤
│  Raw Data:                                                      │
│  • income_statements (15 years annual, 20 quarters)             │
│  • balance_sheets (15 years annual)                             │
│  • cash_flows (15 years annual)                                 │
│  • prices (5 years daily)                                       │
│  • insider_trades (100 records)                                 │
│  • 13-F holdings (3 years quarterly)                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Python Processing Layer                                         │
├─────────────────────────────────────────────────────────────────┤
│  Calculations:                                                  │
│  • Piotroski F-Score (9 criteria)                               │
│  • Altman Z-Score (5 ratios)                                    │
│  • Beneish M-Score (8 variables)                                │
│  • Owner Earnings (Buffett)                                     │
│  • ROIC / CROIC                                                 │
│  • Graham Number / NCAV                                         │
│  • Technical indicators (moving averages, RSI)                  │
│  • Valuation metrics (PEG, EV/EBITDA, FCF yield)                │
│  • Growth rates (CAGR, YoY)                                     │
│  • Trend analysis (acceleration/deceleration)                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Structured Output for LLM Experts                               │
├─────────────────────────────────────────────────────────────────┤
│  Per-Expert Data Packets:                                       │
│  • Pre-calculated scores with component breakdowns              │
│  • Historical trends with annotations                           │
│  • Peer comparisons where relevant                              │
│  • Risk flags and anomaly detection                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Professional Metrics & Formulas

### 1. Piotroski F-Score (9 Criteria)

**Purpose:** Assess financial strength for value investing (Graham, Buffett)
**Score Range:** 0-9 (higher = stronger)
**Interpretation:** 8-9 = Very Strong, 7 = Strong, 4-6 = Average, 0-3 = Weak

#### Profitability (4 signals)

| Criterion | Formula | Score = 1 if |
|-----------|---------|--------------|
| **ROA** | Net Income / Beginning Total Assets | > 0 |
| **CFO** | Operating Cash Flow / Beginning Total Assets | > 0 |
| **ΔROA** | ROA(t) - ROA(t-1) | > 0 |
| **Accruals** | CFO/Assets vs Net Income/Assets | CFO/Assets > ROA |

```python
def piotroski_profitability(ni, ocf, total_assets_beg, total_assets_beg_prev, ni_prev, ocf_prev):
    roa = ni / total_assets_beg
    roa_prev = ni_prev / total_assets_beg_prev
    cfo_ratio = ocf / total_assets_beg

    f_roa = 1 if roa > 0 else 0
    f_cfo = 1 if cfo_ratio > 0 else 0
    f_delta_roa = 1 if roa > roa_prev else 0
    f_accrual = 1 if cfo_ratio > roa else 0

    return f_roa + f_cfo + f_delta_roa + f_accrual
```

#### Leverage/Liquidity (3 signals)

| Criterion | Formula | Score = 1 if |
|-----------|---------|--------------|
| **ΔLEVER** | LT Debt/Avg Assets change | Decreased YoY |
| **ΔLIQUID** | Current Ratio change | Increased YoY |
| **EQ_OFFER** | Shares Outstanding change | Same or fewer shares |

```python
def piotroski_leverage(lt_debt, lt_debt_prev, avg_assets, avg_assets_prev,
                       current_assets, current_liab, ca_prev, cl_prev,
                       shares_out, shares_out_prev):
    lever_ratio = lt_debt / avg_assets
    lever_ratio_prev = lt_debt_prev / avg_assets_prev
    current_ratio = current_assets / current_liab
    current_ratio_prev = ca_prev / cl_prev

    f_lever = 1 if lever_ratio < lever_ratio_prev else 0
    f_liquid = 1 if current_ratio > current_ratio_prev else 0
    f_eq_offer = 1 if shares_out <= shares_out_prev else 0

    return f_lever + f_liquid + f_eq_offer
```

#### Operating Efficiency (2 signals)

| Criterion | Formula | Score = 1 if |
|-----------|---------|--------------|
| **ΔMARGIN** | Gross Margin change | Increased YoY |
| **ΔTURN** | Asset Turnover change | Increased YoY |

```python
def piotroski_efficiency(gross_profit, revenue, gp_prev, rev_prev,
                         total_assets_beg, total_assets_beg_prev):
    gross_margin = gross_profit / revenue
    gross_margin_prev = gp_prev / rev_prev
    asset_turn = revenue / total_assets_beg
    asset_turn_prev = rev_prev / total_assets_beg_prev

    f_margin = 1 if gross_margin > gross_margin_prev else 0
    f_turn = 1 if asset_turn > asset_turn_prev else 0

    return f_margin + f_turn
```

**Data Required:**
- Income Statement: net_income, revenue, gross_profit
- Balance Sheet: total_assets, current_assets, current_liabilities, long_term_debt, shares_outstanding
- Cash Flow: operating_cash_flow

---

### 2. Altman Z-Score (5 Ratios)

**Purpose:** Predict bankruptcy probability (Dalio, Burry)
**Interpretation:**
- Z > 3.0: Safe zone
- Z 2.7-3.0: Grey zone (probably safe)
- Z 1.8-2.7: Grey zone (caution)
- Z < 1.8: Distress zone

#### Original Formula (Public Manufacturing)

**Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 0.99×X5**

| Ratio | Formula | Measures |
|-------|---------|----------|
| **X1** | Working Capital / Total Assets | Liquidity |
| **X2** | Retained Earnings / Total Assets | Profitability & Age |
| **X3** | EBIT / Total Assets | Operating Efficiency |
| **X4** | Market Cap / Total Liabilities | Market Dimension |
| **X5** | Revenue / Total Assets | Asset Turnover |

```python
def altman_z_score(working_capital, retained_earnings, ebit,
                   market_cap, revenue, total_assets, total_liabilities):
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities
    x5 = revenue / total_assets

    z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 0.99*x5

    if z > 3.0:
        zone = "safe"
    elif z > 2.7:
        zone = "grey_upper"
    elif z > 1.8:
        zone = "grey_lower"
    else:
        zone = "distress"

    return {
        "z_score": z,
        "zone": zone,
        "components": {"x1": x1, "x2": x2, "x3": x3, "x4": x4, "x5": x5}
    }
```

#### Non-Manufacturing Formula (Z")

**Z" = 6.56×X1 + 3.26×X2 + 6.72×X3 + 1.05×X4**

(Excludes X5 to minimize industry effect)

**Data Required:**
- Balance Sheet: current_assets, current_liabilities, retained_earnings, total_assets, total_liabilities
- Income Statement: ebit, revenue
- Market: market_cap

---

### 3. Beneish M-Score (8 Variables)

**Purpose:** Detect earnings manipulation (Burry forensic analysis)
**Threshold:** M > -1.78 suggests likely manipulation
**Note:** Correctly identified Enron as manipulator in 1998

**M = −4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI + 0.115×DEPI − 0.172×SGAI + 4.679×TATA − 0.327×LVGI**

| Variable | Formula | Red Flag if |
|----------|---------|-------------|
| **DSRI** | (Receivables/Revenue)_t / (Receivables/Revenue)_t-1 | > 1 |
| **GMI** | Gross_Margin_t-1 / Gross_Margin_t | > 1 |
| **AQI** | (1 - (CA + PPE + Securities) / TA)_t / (same)_t-1 | > 1 |
| **SGI** | Revenue_t / Revenue_t-1 | High growth |
| **DEPI** | Depreciation_Rate_t-1 / Depreciation_Rate_t | > 1 |
| **SGAI** | (SGA/Revenue)_t / (SGA/Revenue)_t-1 | > 1 |
| **LVGI** | (Debt/Assets)_t / (Debt/Assets)_t-1 | > 1 |
| **TATA** | (Working Capital Change - D&A) / Total Assets | High |

```python
def beneish_m_score(receivables, receivables_prev, revenue, revenue_prev,
                    gross_profit, gross_profit_prev, current_assets, ppe,
                    securities, total_assets, ca_prev, ppe_prev, sec_prev,
                    ta_prev, depreciation, depreciation_prev, sga, sga_prev,
                    total_debt, td_prev, wc_change, da):

    # Days Sales in Receivables Index
    dsri = (receivables / revenue) / (receivables_prev / revenue_prev)

    # Gross Margin Index
    gm = gross_profit / revenue
    gm_prev = gross_profit_prev / revenue_prev
    gmi = gm_prev / gm if gm != 0 else 1

    # Asset Quality Index
    aq = 1 - (current_assets + ppe + securities) / total_assets
    aq_prev = 1 - (ca_prev + ppe_prev + sec_prev) / ta_prev
    aqi = aq / aq_prev if aq_prev != 0 else 1

    # Sales Growth Index
    sgi = revenue / revenue_prev

    # Depreciation Index
    dep_rate = depreciation / (depreciation + ppe)
    dep_rate_prev = depreciation_prev / (depreciation_prev + ppe_prev)
    depi = dep_rate_prev / dep_rate if dep_rate != 0 else 1

    # SGA Index
    sgai = (sga / revenue) / (sga_prev / revenue_prev)

    # Leverage Index
    lvgi = (total_debt / total_assets) / (td_prev / ta_prev)

    # Total Accruals to Total Assets
    tata = (wc_change - da) / total_assets

    m_score = (-4.84 + 0.92*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi
               + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi)

    return {
        "m_score": m_score,
        "likely_manipulator": m_score > -1.78,
        "components": {
            "dsri": dsri, "gmi": gmi, "aqi": aqi, "sgi": sgi,
            "depi": depi, "sgai": sgai, "lvgi": lvgi, "tata": tata
        },
        "red_flags": [
            "dsri" if dsri > 1.05 else None,
            "gmi" if gmi > 1.04 else None,
            "aqi" if aqi > 1.0 else None,
            "tata" if tata > 0.05 else None
        ]
    }
```

**Data Required:**
- Income Statement: revenue, gross_profit, sga_expense, depreciation
- Balance Sheet: accounts_receivable, current_assets, ppe, securities, total_assets, total_debt
- Cash Flow: changes in working capital

---

### 4. Owner Earnings (Buffett)

**Purpose:** Calculate true cash generation capacity
**Formula:** Net Income + Non-Cash Charges - Maintenance CapEx

```python
def owner_earnings(net_income, depreciation, amortization, other_noncash,
                   capex, revenue, revenue_prev, avg_ppe_to_sales_7yr):
    """
    Buffett's Owner Earnings calculation.
    Uses Greenwald method to estimate maintenance CapEx.
    """
    non_cash_charges = depreciation + amortization + other_noncash

    # Greenwald method for maintenance CapEx
    revenue_growth = revenue - revenue_prev
    growth_capex = avg_ppe_to_sales_7yr * revenue_growth
    maintenance_capex = capex - growth_capex

    # Conservative: use full capex if maintenance estimate is negative
    maintenance_capex = max(maintenance_capex, capex * 0.5)

    owners_earnings = net_income + non_cash_charges - maintenance_capex

    return {
        "owners_earnings": owners_earnings,
        "ocf_approximation": net_income + non_cash_charges - capex,  # Conservative
        "components": {
            "net_income": net_income,
            "non_cash_charges": non_cash_charges,
            "total_capex": capex,
            "maintenance_capex_est": maintenance_capex,
            "growth_capex_est": growth_capex
        }
    }
```

---

### 5. ROIC (Return on Invested Capital)

**Purpose:** Measure value creation vs. cost of capital
**Interpretation:** ROIC > WACC = Value creation

```python
def roic(ebit, tax_rate, total_equity, total_debt, cash,
         ebit_prev, equity_prev, debt_prev, cash_prev):
    """
    ROIC = NOPAT / Average Invested Capital
    """
    nopat = ebit * (1 - tax_rate)

    # Invested Capital = Equity + Debt - Cash
    ic_current = total_equity + total_debt - cash
    ic_prev = equity_prev + debt_prev - cash_prev
    avg_invested_capital = (ic_current + ic_prev) / 2

    roic_value = nopat / avg_invested_capital if avg_invested_capital > 0 else 0

    return {
        "roic": roic_value,
        "nopat": nopat,
        "avg_invested_capital": avg_invested_capital,
        "interpretation": (
            "excellent" if roic_value > 0.20 else
            "good" if roic_value > 0.15 else
            "average" if roic_value > 0.10 else
            "poor"
        )
    }
```

---

### 6. Graham Number & NCAV

**Purpose:** Conservative intrinsic value estimates (Graham)

```python
def graham_number(eps, book_value_per_share):
    """
    Graham Number = sqrt(22.5 × EPS × BVPS)
    Fair value estimate based on earnings and book value.
    """
    if eps <= 0 or book_value_per_share <= 0:
        return None
    return (22.5 * eps * book_value_per_share) ** 0.5

def ncav_per_share(current_assets, total_liabilities, preferred_stock, shares_outstanding):
    """
    Net Current Asset Value = (Current Assets - Total Liabilities) / Shares
    Buy at 2/3 of NCAV for 33% margin of safety.
    """
    ncav = current_assets - total_liabilities - preferred_stock
    ncav_per_share = ncav / shares_outstanding

    return {
        "ncav_per_share": ncav_per_share,
        "buy_below": ncav_per_share * 0.67,  # Graham's 2/3 rule
        "total_ncav": ncav
    }

def graham_conservative_ncav(cash, receivables, inventory, total_liabilities,
                             preferred_stock, shares_outstanding):
    """
    Conservative NCAV with liquidation discounts.
    Cash: 100%, Receivables: 75%, Inventory: 50%
    """
    adjusted_assets = cash + (0.75 * receivables) + (0.5 * inventory)
    ncav = adjusted_assets - total_liabilities - preferred_stock

    return ncav / shares_outstanding
```

---

### 7. Valuation Metrics

```python
def valuation_metrics(price, eps, eps_growth_rate, revenue, ebitda,
                      fcf, shares_out, total_debt, cash):
    """
    Standard valuation ratios.
    """
    market_cap = price * shares_out
    enterprise_value = market_cap + total_debt - cash

    return {
        "pe_ratio": price / eps if eps > 0 else None,
        "peg_ratio": (price / eps) / (eps_growth_rate * 100) if eps > 0 and eps_growth_rate > 0 else None,
        "price_to_sales": market_cap / revenue if revenue > 0 else None,
        "ev_to_ebitda": enterprise_value / ebitda if ebitda > 0 else None,
        "ev_to_revenue": enterprise_value / revenue if revenue > 0 else None,
        "fcf_yield": (fcf / market_cap) * 100 if market_cap > 0 else None,
        "earnings_yield": (eps / price) * 100 if price > 0 else None
    }
```

---

### 8. Growth & Trend Analysis

```python
def cagr(beginning_value, ending_value, years):
    """Compound Annual Growth Rate"""
    if beginning_value <= 0 or ending_value <= 0 or years <= 0:
        return None
    return (ending_value / beginning_value) ** (1 / years) - 1

def growth_trend(values_by_year):
    """
    Analyze growth trajectory.
    Returns: accelerating, decelerating, steady, volatile
    """
    if len(values_by_year) < 3:
        return {"trend": "insufficient_data"}

    growth_rates = []
    for i in range(1, len(values_by_year)):
        if values_by_year[i-1] != 0:
            growth_rates.append(
                (values_by_year[i] - values_by_year[i-1]) / abs(values_by_year[i-1])
            )

    # Check if growth is accelerating or decelerating
    recent_avg = sum(growth_rates[-3:]) / 3 if len(growth_rates) >= 3 else growth_rates[-1]
    earlier_avg = sum(growth_rates[:3]) / 3 if len(growth_rates) >= 6 else growth_rates[0]

    # Calculate volatility
    avg_growth = sum(growth_rates) / len(growth_rates)
    variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
    volatility = variance ** 0.5

    if volatility > 0.3:
        trend = "volatile"
    elif recent_avg > earlier_avg * 1.2:
        trend = "accelerating"
    elif recent_avg < earlier_avg * 0.8:
        trend = "decelerating"
    else:
        trend = "steady"

    return {
        "trend": trend,
        "cagr": cagr(values_by_year[0], values_by_year[-1], len(values_by_year) - 1),
        "recent_growth": recent_avg,
        "volatility": volatility,
        "growth_rates": growth_rates
    }
```

---

## Expert-Specific Pre-Calculations

### Warren Buffett
- Owner Earnings (5, 10, 15 year averages)
- ROIC with trend
- Moat indicators (gross margin stability, market share)
- Management efficiency (SGA/Revenue trend)
- Debt service coverage

### Ben Graham
- Graham Number
- NCAV (standard and conservative)
- 7 Defensive Investor criteria
- Earnings stability (no losses in 10 years)
- Dividend record

### Peter Lynch
- PEG Ratio
- Stock classification (growth rate buckets)
- Earnings acceleration/deceleration
- Same-store sales growth (if applicable)
- Institutional ownership %

### Cathie Wood
- Revenue CAGR (5 year)
- Addressable market growth
- R&D intensity (R&D/Revenue)
- Gross margin trajectory
- Customer acquisition trends

### George Soros
- Price momentum (50/200 DMA)
- Relative strength vs. sector
- Sentiment indicators from news
- Reflexivity signals (price/fundamental divergence)
- Volatility metrics

### Ray Dalio
- Altman Z-Score
- Debt/EBITDA ratio
- Interest coverage trends
- Cycle positioning indicators
- Stress test scenarios

### Michael Burry
- Beneish M-Score
- Piotroski F-Score
- Accruals ratio
- DSO trends
- Revenue vs. Cash flow divergence
- Insider trading patterns

---

## Data Windows (Extended)

| Data Type | Window | Rationale |
|-----------|--------|-----------|
| Income Statements (Annual) | 15 years | Full business cycle coverage |
| Income Statements (Quarterly) | 20 quarters | Seasonal patterns + recent trends |
| Balance Sheets | 15 years | Long-term capital structure trends |
| Cash Flow Statements | 15 years | Cash generation consistency |
| Price History | 5 years | Medium-term technical context |
| 13-F Holdings | 3 years (12 quarters) | Position building/reduction patterns |
| Insider Trades | 100 records | Recent management sentiment |

---

## Implementation Notes

1. **Error Handling:** All calculations should gracefully handle missing data
2. **Null Propagation:** If a component is missing, flag it rather than skip
3. **Historical Comparison:** Include YoY and multi-year comparisons
4. **Sector Context:** Where possible, compare to sector medians
5. **Confidence Scoring:** Weight calculations by data completeness

---

## Sources

- [Piotroski F-Score - Wikipedia](https://en.wikipedia.org/wiki/Piotroski_F-score)
- [Altman Z-Score - Wall Street Prep](https://www.wallstreetprep.com/knowledge/altman-z-score/)
- [Beneish M-Score - StableBread](https://stablebread.com/beneish-m-score/)
- [Owner Earnings - StableBread](https://stablebread.com/warren-buffett-owners-earnings/)
- [ROIC - Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/accounting/return-on-invested-capital/)
- [Graham NCAV - Net Net Hunter](https://www.netnethunter.com/grahams-net-current-assets-formula/)
