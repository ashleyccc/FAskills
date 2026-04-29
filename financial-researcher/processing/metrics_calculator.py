"""
Professional Financial Metrics Calculator v2.0

This module calculates metrics that financialdatasets.ai does NOT provide:
- Composite scores (Piotroski, Altman, Ohlson, Beneish, Magic Formula)
- Quality metrics (Sloan Accrual, Gross Profitability, FCF Conversion)
- Shareholder return metrics (Shareholder Yield, Buyback Yield)
- Value creation (EVA, Owner Earnings)
- Decomposition (DuPont 5-factor)
- Growth analysis (Sustainable Growth Rate, trends)
- Benchmarking (industry percentiles, z-scores)

Metrics that financialdatasets.ai ALREADY provides (don't recalculate):
- ROIC, ROE, ROA
- P/E, P/B, P/S, EV/EBITDA, PEG
- Profit margins (gross, operating, net)
- Liquidity ratios (current, quick)
- Leverage ratios (D/E, interest coverage)
- Growth rates (revenue, EPS, FCF)
- Efficiency ratios (asset turnover, DSO)

Sources:
- Piotroski F-Score: Stanford (2000)
- Altman Z-Score: NYU (1968)
- Ohlson O-Score: NYU (1980)
- Beneish M-Score: Indiana (1999)
- Sloan Accrual: U Michigan (1996)
- Owner Earnings: Buffett/Berkshire Letters
- Shareholder Yield: Priest (2005)
- AQR Quality: Asness, Frazzini, Pedersen (2014)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import math
from statistics import median, stdev, mean


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class ScoreInterpretation(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    DANGEROUS = "dangerous"


class Trend(Enum):
    STRONG_UP = "strong_up"
    UP = "up"
    STABLE = "stable"
    DOWN = "down"
    STRONG_DOWN = "strong_down"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class MetricResult:
    """Generic result container with value, interpretation, and components."""
    value: float
    interpretation: str
    components: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    data_quality: float = 1.0  # 0-1, how complete was the input data


@dataclass
class BenchmarkResult:
    """Result with industry/peer comparison."""
    raw_value: float
    percentile: float  # 0-100
    z_score: float  # vs industry
    vs_median: float  # % difference from median
    interpretation: str


# =============================================================================
# 1. COMPOSITE SCORES
# =============================================================================

def piotroski_f_score(
    # Current year
    net_income: float,
    operating_cash_flow: float,
    total_assets: float,
    long_term_debt: float,
    current_assets: float,
    current_liabilities: float,
    shares_outstanding: float,
    gross_profit: float,
    revenue: float,
    # Previous year
    net_income_prev: float,
    total_assets_prev: float,
    long_term_debt_prev: float,
    current_assets_prev: float,
    current_liabilities_prev: float,
    shares_outstanding_prev: float,
    gross_profit_prev: float,
    revenue_prev: float,
) -> MetricResult:
    """
    Piotroski F-Score: 9-point financial strength assessment.

    Score 8-9: Very strong (buy)
    Score 7: Strong
    Score 4-6: Average
    Score 0-3: Weak (avoid)
    """
    components = {}
    flags = []

    # Safely calculate ratios
    def safe_div(a, b, default=0):
        return a / b if b and b != 0 else default

    # PROFITABILITY (4 points)
    roa = safe_div(net_income, total_assets)
    roa_prev = safe_div(net_income_prev, total_assets_prev)
    cfo_ratio = safe_div(operating_cash_flow, total_assets)

    components['f1_roa_positive'] = 1 if roa > 0 else 0
    components['f2_cfo_positive'] = 1 if cfo_ratio > 0 else 0
    components['f3_roa_improving'] = 1 if roa > roa_prev else 0
    components['f4_accruals_quality'] = 1 if cfo_ratio > roa else 0  # CFO > NI means quality earnings

    if roa <= 0:
        flags.append("Negative ROA - unprofitable")
    if cfo_ratio <= roa and roa > 0:
        flags.append("CFO < Net Income - potential earnings quality issue")

    # LEVERAGE/LIQUIDITY (3 points)
    leverage = safe_div(long_term_debt, total_assets)
    leverage_prev = safe_div(long_term_debt_prev, total_assets_prev)
    current_ratio = safe_div(current_assets, current_liabilities)
    current_ratio_prev = safe_div(current_assets_prev, current_liabilities_prev)

    components['f5_leverage_decreasing'] = 1 if leverage < leverage_prev else 0
    components['f6_liquidity_improving'] = 1 if current_ratio > current_ratio_prev else 0
    components['f7_no_dilution'] = 1 if shares_outstanding <= shares_outstanding_prev else 0

    if shares_outstanding > shares_outstanding_prev * 1.05:
        flags.append(f"Significant dilution: {(shares_outstanding/shares_outstanding_prev - 1)*100:.1f}% more shares")

    # EFFICIENCY (2 points)
    gross_margin = safe_div(gross_profit, revenue)
    gross_margin_prev = safe_div(gross_profit_prev, revenue_prev)
    asset_turnover = safe_div(revenue, total_assets)
    asset_turnover_prev = safe_div(revenue_prev, total_assets_prev)

    components['f8_margin_improving'] = 1 if gross_margin > gross_margin_prev else 0
    components['f9_turnover_improving'] = 1 if asset_turnover > asset_turnover_prev else 0

    # Total score
    f_score = sum(components.values())

    if f_score >= 8:
        interpretation = "Very Strong - High quality, consider buying"
    elif f_score >= 7:
        interpretation = "Strong - Good financial health"
    elif f_score >= 4:
        interpretation = "Average - Mixed signals"
    else:
        interpretation = "Weak - Poor financial health, avoid"

    return MetricResult(
        value=f_score,
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def altman_z_score(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    revenue: float,
    total_assets: float,
    total_liabilities: float,
    is_manufacturing: bool = True
) -> MetricResult:
    """
    Altman Z-Score: Bankruptcy prediction model.

    Manufacturing:
    - Z > 2.99: Safe zone
    - Z 1.81-2.99: Grey zone
    - Z < 1.81: Distress zone

    Non-manufacturing:
    - Z > 2.60: Safe zone
    - Z 1.10-2.60: Grey zone
    - Z < 1.10: Distress zone
    """
    flags = []

    if total_assets == 0:
        return MetricResult(value=0, interpretation="Cannot calculate - no assets", flags=["Missing data"])

    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities if total_liabilities > 0 else 10  # Cap at reasonable value
    x5 = revenue / total_assets

    components = {
        "x1_working_capital_ratio": round(x1, 4),
        "x2_retained_earnings_ratio": round(x2, 4),
        "x3_ebit_ratio": round(x3, 4),
        "x4_market_to_liabilities": round(x4, 4),
        "x5_asset_turnover": round(x5, 4)
    }

    if is_manufacturing:
        z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 0.999*x5
        if z > 2.99:
            interpretation = "Safe Zone - Low bankruptcy risk"
        elif z > 1.81:
            interpretation = "Grey Zone - Moderate risk, monitor closely"
            flags.append("In grey zone - elevated bankruptcy risk")
        else:
            interpretation = "Distress Zone - High bankruptcy risk"
            flags.append("DISTRESS: High probability of bankruptcy within 2 years")
    else:
        # Z'' model for non-manufacturing
        z = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
        if z > 2.60:
            interpretation = "Safe Zone - Low bankruptcy risk"
        elif z > 1.10:
            interpretation = "Grey Zone - Moderate risk"
            flags.append("In grey zone - elevated bankruptcy risk")
        else:
            interpretation = "Distress Zone - High bankruptcy risk"
            flags.append("DISTRESS: High probability of bankruptcy")

    # Flag specific weaknesses
    if x1 < 0:
        flags.append("Negative working capital")
    if x2 < 0:
        flags.append("Accumulated deficit (negative retained earnings)")
    if x3 < 0:
        flags.append("Operating losses (negative EBIT)")

    return MetricResult(
        value=round(z, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def ohlson_o_score(
    total_assets: float,
    total_liabilities: float,
    working_capital: float,
    current_liabilities: float,
    net_income: float,
    funds_from_operations: float,  # Usually OCF or NI + D&A
    net_income_prev: float,
    total_liabilities_prev: float,
    gnp_deflator: float = 1.0  # Inflation adjustment, default to 1
) -> MetricResult:
    """
    Ohlson O-Score: 9-factor logistic bankruptcy model (1980).
    More accurate than Altman Z for recent periods.

    O > 0.5: High probability of bankruptcy
    O < 0.5: Lower probability

    The output is a probability (0-1) after logistic transformation.
    """
    flags = []

    if total_assets == 0:
        return MetricResult(value=1.0, interpretation="Cannot calculate", flags=["Missing data"])

    # Adjust for size (log of assets relative to GNP deflator)
    log_ta_gnp = math.log(total_assets / gnp_deflator) if total_assets > 0 else 0

    # Ratios
    tlta = total_liabilities / total_assets  # Total liabilities / Total assets
    wcta = working_capital / total_assets  # Working capital / Total assets
    clca = current_liabilities / (working_capital + current_liabilities) if (working_capital + current_liabilities) > 0 else 1

    # Binary: 1 if liabilities > assets
    oeneg = 1 if total_liabilities > total_assets else 0

    nita = net_income / total_assets  # Net income / Total assets
    ffota = funds_from_operations / total_liabilities if total_liabilities > 0 else 0

    # Binary: 1 if net income was negative for last two years
    intwo = 1 if net_income < 0 and net_income_prev < 0 else 0

    # Change in net income
    delta_ni = net_income - net_income_prev
    chin = delta_ni / (abs(net_income) + abs(net_income_prev)) if (abs(net_income) + abs(net_income_prev)) > 0 else 0

    components = {
        "log_ta_gnp": round(log_ta_gnp, 4),
        "tlta": round(tlta, 4),
        "wcta": round(wcta, 4),
        "clca": round(clca, 4),
        "oeneg": oeneg,
        "nita": round(nita, 4),
        "ffota": round(ffota, 4),
        "intwo": intwo,
        "chin": round(chin, 4)
    }

    # O-Score calculation
    o_score = (
        -1.32
        - 0.407 * log_ta_gnp
        + 6.03 * tlta
        - 1.43 * wcta
        + 0.0757 * clca
        - 2.37 * nita
        - 1.83 * ffota
        + 0.285 * intwo
        - 1.72 * oeneg
        - 0.521 * chin
    )

    # Convert to probability
    probability = 1 / (1 + math.exp(-o_score))

    if probability > 0.5:
        interpretation = f"High bankruptcy probability ({probability:.1%})"
        flags.append("HIGH RISK: Ohlson model indicates >50% bankruptcy probability")
    elif probability > 0.3:
        interpretation = f"Elevated bankruptcy risk ({probability:.1%})"
        flags.append("Elevated bankruptcy risk - monitor closely")
    else:
        interpretation = f"Lower bankruptcy risk ({probability:.1%})"

    if oeneg == 1:
        flags.append("Liabilities exceed assets (technically insolvent)")
    if intwo == 1:
        flags.append("Two consecutive years of losses")

    return MetricResult(
        value=round(probability, 4),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def beneish_m_score(
    # Current year
    receivables: float,
    revenue: float,
    gross_profit: float,
    total_assets: float,
    ppe: float,
    depreciation: float,
    sga: float,
    total_debt: float,
    current_assets: float,
    current_liabilities: float,
    # Previous year
    receivables_prev: float,
    revenue_prev: float,
    gross_profit_prev: float,
    total_assets_prev: float,
    ppe_prev: float,
    depreciation_prev: float,
    sga_prev: float,
    total_debt_prev: float,
    # For TATA
    net_income: float,
    operating_cash_flow: float,
) -> MetricResult:
    """
    Beneish M-Score: 8-variable earnings manipulation detector.

    M > -1.78: Likely manipulator
    M < -2.22: Unlikely manipulator
    M between: Grey zone

    Correctly identified Enron as manipulator in 1998.
    """
    flags = []

    def safe_div(a, b, default=1.0):
        return a / b if b and b != 0 else default

    # DSRI: Days Sales in Receivables Index
    dsr = safe_div(receivables, revenue)
    dsr_prev = safe_div(receivables_prev, revenue_prev)
    dsri = safe_div(dsr, dsr_prev)

    # GMI: Gross Margin Index
    gm = safe_div(gross_profit, revenue)
    gm_prev = safe_div(gross_profit_prev, revenue_prev)
    gmi = safe_div(gm_prev, gm)  # Note: inverted - higher means margin declined

    # AQI: Asset Quality Index
    hard_assets = current_assets + ppe
    aq = 1 - safe_div(hard_assets, total_assets)
    hard_assets_prev = current_assets + ppe_prev  # Simplified
    aq_prev = 1 - safe_div(hard_assets_prev, total_assets_prev)
    aqi = safe_div(aq, aq_prev)

    # SGI: Sales Growth Index
    sgi = safe_div(revenue, revenue_prev)

    # DEPI: Depreciation Index
    dep_rate = safe_div(depreciation, depreciation + ppe)
    dep_rate_prev = safe_div(depreciation_prev, depreciation_prev + ppe_prev)
    depi = safe_div(dep_rate_prev, dep_rate)

    # SGAI: SG&A Index
    sga_ratio = safe_div(sga, revenue)
    sga_ratio_prev = safe_div(sga_prev, revenue_prev)
    sgai = safe_div(sga_ratio, sga_ratio_prev)

    # LVGI: Leverage Index
    lev = safe_div(total_debt, total_assets)
    lev_prev = safe_div(total_debt_prev, total_assets_prev)
    lvgi = safe_div(lev, lev_prev)

    # TATA: Total Accruals to Total Assets
    accruals = net_income - operating_cash_flow
    tata = safe_div(accruals, total_assets)

    components = {
        "dsri": round(dsri, 3),
        "gmi": round(gmi, 3),
        "aqi": round(aqi, 3),
        "sgi": round(sgi, 3),
        "depi": round(depi, 3),
        "sgai": round(sgai, 3),
        "lvgi": round(lvgi, 3),
        "tata": round(tata, 3)
    }

    # M-Score formula
    m_score = (
        -4.84
        + 0.920 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )

    # Interpretation and flags
    if dsri > 1.05:
        flags.append(f"DSRI={dsri:.2f}: Receivables growing faster than revenue")
    if gmi > 1.04:
        flags.append(f"GMI={gmi:.2f}: Gross margin deteriorating")
    if aqi > 1.0:
        flags.append(f"AQI={aqi:.2f}: Asset quality declining (more soft assets)")
    if depi > 1.0:
        flags.append(f"DEPI={depi:.2f}: Depreciation slowing (extending asset lives)")
    if tata > 0.05:
        flags.append(f"TATA={tata:.2f}: High accruals - earnings quality concern")
    if sgi > 1.5:
        flags.append(f"SGI={sgi:.2f}: Very high sales growth - scrutinize quality")

    if m_score > -1.78:
        interpretation = f"LIKELY MANIPULATOR (M={m_score:.2f} > -1.78)"
        flags.insert(0, "⚠️ HIGH MANIPULATION RISK - Investigate earnings quality")
    elif m_score > -2.22:
        interpretation = f"Grey Zone (M={m_score:.2f}) - Some concern"
    else:
        interpretation = f"Unlikely Manipulator (M={m_score:.2f})"

    return MetricResult(
        value=round(m_score, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def magic_formula_rank(
    ebit: float,
    enterprise_value: float,
    total_equity: float,
    total_debt: float,
    cash: float,
    ppe_net: float,
    working_capital: float,
) -> MetricResult:
    """
    Greenblatt Magic Formula: Combines ROIC rank + Earnings Yield rank.

    Lower combined rank = better stock.

    Earnings Yield = EBIT / Enterprise Value
    ROIC = EBIT / (Net Fixed Assets + Working Capital)
    """
    flags = []

    # Earnings Yield (higher is better)
    earnings_yield = ebit / enterprise_value if enterprise_value > 0 else 0

    # Tangible Capital = Net Fixed Assets + Net Working Capital
    tangible_capital = ppe_net + working_capital
    roic = ebit / tangible_capital if tangible_capital > 0 else 0

    components = {
        "earnings_yield": round(earnings_yield * 100, 2),  # As percentage
        "roic": round(roic * 100, 2),  # As percentage
        "tangible_capital": tangible_capital
    }

    # Interpretation (without actual ranking against universe)
    if earnings_yield > 0.15 and roic > 0.25:
        interpretation = "Strong Magic Formula candidate - high yield and ROIC"
    elif earnings_yield > 0.10 and roic > 0.15:
        interpretation = "Good Magic Formula candidate"
    elif earnings_yield > 0.05 and roic > 0.10:
        interpretation = "Average - moderate yield and ROIC"
    else:
        interpretation = "Weak Magic Formula candidate"

    if earnings_yield < 0:
        flags.append("Negative earnings yield - unprofitable or overvalued")
    if roic < 0:
        flags.append("Negative ROIC - destroying capital")

    # Combined score (higher is better for this simplified version)
    combined_score = (earnings_yield * 100) + (roic * 100)

    return MetricResult(
        value=round(combined_score, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 2. QUALITY METRICS
# =============================================================================

def sloan_accrual_ratio(
    net_income: float,
    operating_cash_flow: float,
    total_assets: float,
    total_assets_prev: float
) -> MetricResult:
    """
    Sloan Accrual Ratio: Earnings quality indicator.

    Accrual Ratio = (Net Income - OCF) / Average Total Assets

    -10% to +10%: Safe zone (quality earnings)
    -25% to -10% or +10% to +25%: Warning zone
    < -25% or > +25%: High accrual - earnings likely manipulated

    Low accrual stocks outperformed by 10% annually (Sloan 1996).
    """
    avg_assets = (total_assets + total_assets_prev) / 2
    accruals = net_income - operating_cash_flow
    accrual_ratio = accruals / avg_assets if avg_assets > 0 else 0

    flags = []

    if -0.10 <= accrual_ratio <= 0.10:
        interpretation = "Safe Zone - Quality earnings backed by cash"
    elif -0.25 <= accrual_ratio < -0.10:
        interpretation = "Warning - Unusual negative accruals"
        flags.append("Investigate: Large negative accruals may indicate write-offs")
    elif 0.10 < accrual_ratio <= 0.25:
        interpretation = "Warning - Elevated accruals"
        flags.append("Accruals building up - earnings may not be sustainable")
    else:
        if accrual_ratio > 0.25:
            interpretation = "DANGER - Very high accruals"
            flags.append("⚠️ HIGH RISK: Earnings heavily based on accruals, not cash")
        else:
            interpretation = "DANGER - Extreme negative accruals"
            flags.append("Investigate: Possible large write-downs or restructuring")

    components = {
        "accruals": accruals,
        "avg_assets": avg_assets,
        "net_income": net_income,
        "operating_cash_flow": operating_cash_flow
    }

    return MetricResult(
        value=round(accrual_ratio * 100, 2),  # As percentage
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def gross_profitability(
    gross_profit: float,
    total_assets: float
) -> MetricResult:
    """
    Novy-Marx Gross Profitability: GP/Assets

    Strong predictor of returns (Novy-Marx 2013).
    Used by Fama-French as profitability factor.

    Higher is better. Compare to industry peers.
    """
    gp_assets = gross_profit / total_assets if total_assets > 0 else 0

    if gp_assets > 0.40:
        interpretation = "Excellent gross profitability"
    elif gp_assets > 0.25:
        interpretation = "Good gross profitability"
    elif gp_assets > 0.15:
        interpretation = "Average gross profitability"
    else:
        interpretation = "Low gross profitability"

    return MetricResult(
        value=round(gp_assets * 100, 2),
        interpretation=interpretation,
        components={"gross_profit": gross_profit, "total_assets": total_assets}
    )


def fcf_conversion(
    free_cash_flow: float,
    ebitda: float,
    net_income: float
) -> MetricResult:
    """
    Free Cash Flow Conversion Ratio.

    FCF/EBITDA: Target >80% (healthy), >100% (excellent)
    FCF/Net Income: Should be >1.0 (Cash Conversion Ratio)

    Low conversion = earnings not turning into cash.
    """
    flags = []

    fcf_to_ebitda = free_cash_flow / ebitda if ebitda > 0 else 0
    fcf_to_ni = free_cash_flow / net_income if net_income > 0 else 0

    components = {
        "fcf_to_ebitda": round(fcf_to_ebitda * 100, 1),
        "fcf_to_net_income": round(fcf_to_ni * 100, 1)
    }

    if fcf_to_ebitda >= 1.0:
        interpretation = "Excellent - FCF exceeds EBITDA"
    elif fcf_to_ebitda >= 0.80:
        interpretation = "Healthy - Strong cash conversion"
    elif fcf_to_ebitda >= 0.50:
        interpretation = "Moderate - Some cash leakage"
        flags.append("Below 80% FCF conversion - investigate working capital or capex")
    else:
        interpretation = "Poor - Weak cash conversion"
        flags.append("⚠️ Low FCF conversion - earnings not translating to cash")

    if fcf_to_ni < 1.0 and net_income > 0:
        flags.append("Cash conversion ratio <1 - cash flow lags earnings")

    return MetricResult(
        value=round(fcf_to_ebitda * 100, 1),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 3. SHAREHOLDER RETURN METRICS
# =============================================================================

def shareholder_yield(
    dividends_paid: float,  # Usually negative in cash flow statement
    shares_repurchased: float,  # Usually negative
    shares_issued: float,  # Usually positive
    debt_repaid: float,  # Usually negative
    market_cap: float
) -> MetricResult:
    """
    Total Shareholder Yield: Dividend + Buyback + Debt Paydown.

    More comprehensive than dividend yield alone.
    Buybacks are tax-efficient and increasingly common.

    Priest (2005): "Dominant driver of future equity returns"
    """
    # Normalize signs (all should be positive for cash returned)
    div_yield = abs(dividends_paid) / market_cap if market_cap > 0 else 0

    # Net buyback = repurchases - issuance
    net_repurchase = abs(shares_repurchased) - abs(shares_issued)
    buyback_yield = net_repurchase / market_cap if market_cap > 0 else 0

    debt_paydown_yield = abs(debt_repaid) / market_cap if market_cap > 0 and debt_repaid < 0 else 0

    total_yield = div_yield + buyback_yield + debt_paydown_yield

    components = {
        "dividend_yield": round(div_yield * 100, 2),
        "buyback_yield": round(buyback_yield * 100, 2),
        "debt_paydown_yield": round(debt_paydown_yield * 100, 2)
    }

    flags = []

    if buyback_yield < 0:
        flags.append(f"Net issuance of {abs(buyback_yield)*100:.1f}% - diluting shareholders")

    if total_yield > 0.08:
        interpretation = "Excellent shareholder yield (>8%)"
    elif total_yield > 0.05:
        interpretation = "Good shareholder yield (5-8%)"
    elif total_yield > 0.02:
        interpretation = "Moderate shareholder yield (2-5%)"
    elif total_yield > 0:
        interpretation = "Low shareholder yield (<2%)"
    else:
        interpretation = "Negative - Net cash drain from shareholders"
        flags.append("Negative shareholder yield - company taking cash from shareholders")

    return MetricResult(
        value=round(total_yield * 100, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 4. VALUE CREATION METRICS
# =============================================================================

def economic_value_added(
    nopat: float,  # EBIT * (1 - tax_rate)
    invested_capital: float,  # Equity + Debt - Cash
    wacc: float  # Weighted average cost of capital (as decimal, e.g., 0.10)
) -> MetricResult:
    """
    EVA = NOPAT - (Invested Capital × WACC)

    Positive EVA: Creating value above cost of capital
    Negative EVA: Destroying value

    Stern Stewart metric for true economic profit.
    """
    capital_charge = invested_capital * wacc
    eva = nopat - capital_charge

    eva_margin = eva / invested_capital if invested_capital > 0 else 0
    spread = (nopat / invested_capital) - wacc if invested_capital > 0 else 0

    components = {
        "nopat": nopat,
        "invested_capital": invested_capital,
        "wacc": round(wacc * 100, 2),
        "capital_charge": capital_charge,
        "roic_minus_wacc": round(spread * 100, 2)
    }

    flags = []

    if eva > 0:
        interpretation = f"Creating value: ${eva:,.0f} above cost of capital"
    else:
        interpretation = f"Destroying value: ${abs(eva):,.0f} below cost of capital"
        flags.append("⚠️ Negative EVA - returns below cost of capital")

    return MetricResult(
        value=eva,
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def owner_earnings(
    net_income: float,
    depreciation: float,
    amortization: float,
    capex: float,
    working_capital_change: float,
    shares_outstanding: float
) -> MetricResult:
    """
    Buffett's Owner Earnings: True cash available to owners.

    Owner Earnings = Net Income + D&A - Maintenance CapEx - WC increase

    Conservative approach: Use full CapEx as proxy for maintenance.
    """
    # Conservative: assume all CapEx is maintenance
    owner_earnings_conservative = net_income + depreciation + amortization - capex - working_capital_change

    # Less conservative: assume 70% of CapEx is maintenance
    maintenance_capex_estimate = capex * 0.7
    owner_earnings_adjusted = net_income + depreciation + amortization - maintenance_capex_estimate - working_capital_change

    per_share = owner_earnings_conservative / shares_outstanding if shares_outstanding > 0 else 0

    components = {
        "net_income": net_income,
        "depreciation_amortization": depreciation + amortization,
        "capex": capex,
        "working_capital_change": working_capital_change,
        "owner_earnings_conservative": owner_earnings_conservative,
        "owner_earnings_adjusted": owner_earnings_adjusted,
        "per_share": round(per_share, 2)
    }

    flags = []

    if owner_earnings_conservative < 0:
        flags.append("Negative owner earnings - business consuming cash")

    if owner_earnings_conservative < net_income * 0.5:
        flags.append("Owner earnings significantly below net income - high capital intensity")

    # Compare to net income
    oe_vs_ni = owner_earnings_conservative / net_income if net_income > 0 else 0

    if oe_vs_ni > 1.0:
        interpretation = "Owner earnings exceed net income - high quality"
    elif oe_vs_ni > 0.7:
        interpretation = "Owner earnings track net income well"
    elif oe_vs_ni > 0.4:
        interpretation = "Owner earnings lag net income - capital intensive"
    else:
        interpretation = "Owner earnings much lower than net income - question earnings quality"

    return MetricResult(
        value=owner_earnings_conservative,
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 5. DECOMPOSITION ANALYSIS
# =============================================================================

def dupont_5_factor(
    net_income: float,
    ebt: float,  # Earnings before tax
    ebit: float,  # Earnings before interest and tax
    revenue: float,
    total_assets: float,
    shareholders_equity: float
) -> MetricResult:
    """
    DuPont 5-Factor Analysis: Decompose ROE into components.

    ROE = Tax Burden × Interest Burden × EBIT Margin × Asset Turnover × Leverage

    Used by Bloomberg and professional analysts.
    """
    # Calculate components
    tax_burden = net_income / ebt if ebt != 0 else 0  # How much tax takes
    interest_burden = ebt / ebit if ebit != 0 else 0  # How much interest takes
    ebit_margin = ebit / revenue if revenue != 0 else 0  # Operating efficiency
    asset_turnover = revenue / total_assets if total_assets != 0 else 0  # Asset efficiency
    leverage = total_assets / shareholders_equity if shareholders_equity != 0 else 0  # Financial leverage

    # Calculate ROE via components
    roe_decomposed = tax_burden * interest_burden * ebit_margin * asset_turnover * leverage

    # Direct ROE for comparison
    roe_direct = net_income / shareholders_equity if shareholders_equity != 0 else 0

    components = {
        "tax_burden": round(tax_burden, 3),
        "interest_burden": round(interest_burden, 3),
        "ebit_margin": round(ebit_margin * 100, 2),
        "asset_turnover": round(asset_turnover, 3),
        "leverage": round(leverage, 2),
        "roe_decomposed": round(roe_decomposed * 100, 2),
        "roe_direct": round(roe_direct * 100, 2)
    }

    flags = []

    # Identify drivers and concerns
    if leverage > 3.0:
        flags.append(f"High leverage ({leverage:.1f}x) - ROE may be artificially inflated")
    if interest_burden < 0.7:
        flags.append(f"Interest burden ({interest_burden:.0%}) - significant interest expense")
    if tax_burden < 0.6:
        flags.append(f"High effective tax rate ({(1-tax_burden):.0%})")

    interpretation = f"ROE of {roe_direct*100:.1f}% driven by: "
    drivers = []
    if ebit_margin > 0.15:
        drivers.append("strong margins")
    if asset_turnover > 1.0:
        drivers.append("efficient asset use")
    if leverage > 2.0:
        drivers.append("leverage")

    interpretation += ", ".join(drivers) if drivers else "no standout drivers"

    return MetricResult(
        value=round(roe_direct * 100, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 6. GROWTH & SUSTAINABILITY
# =============================================================================

def sustainable_growth_rate(
    roe: float,  # Return on equity (as decimal)
    dividend_payout_ratio: float  # Dividends / Net Income (as decimal)
) -> MetricResult:
    """
    Sustainable Growth Rate: Max growth without new capital.

    SGR = ROE × (1 - Payout Ratio) = ROE × Retention Ratio

    If actual growth > SGR, company needs external financing.
    """
    retention_ratio = 1 - dividend_payout_ratio
    sgr = roe * retention_ratio

    components = {
        "roe": round(roe * 100, 2),
        "retention_ratio": round(retention_ratio * 100, 2),
        "payout_ratio": round(dividend_payout_ratio * 100, 2)
    }

    flags = []

    if sgr > 0.20:
        interpretation = f"High sustainable growth ({sgr*100:.1f}%) - can grow rapidly internally"
    elif sgr > 0.10:
        interpretation = f"Moderate sustainable growth ({sgr*100:.1f}%)"
    elif sgr > 0:
        interpretation = f"Low sustainable growth ({sgr*100:.1f}%) - limited internal growth capacity"
    else:
        interpretation = "Negative SGR - cannot sustain current operations"
        flags.append("⚠️ Negative sustainable growth rate")

    if dividend_payout_ratio > 1.0:
        flags.append("Payout ratio >100% - paying more than earnings (unsustainable)")

    return MetricResult(
        value=round(sgr * 100, 2),
        interpretation=interpretation,
        components=components,
        flags=flags
    )


def analyze_trend(values: List[float], metric_name: str = "metric") -> MetricResult:
    """
    Analyze trend in a time series of values.

    Detects: accelerating, decelerating, stable, volatile
    """
    if len(values) < 3:
        return MetricResult(
            value=0,
            interpretation="Insufficient data for trend analysis",
            flags=["Need at least 3 data points"]
        )

    # Calculate year-over-year growth rates
    growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] != 0:
            gr = (values[i] - values[i-1]) / abs(values[i-1])
            growth_rates.append(gr)

    if len(growth_rates) < 2:
        return MetricResult(value=0, interpretation="Insufficient growth data")

    avg_growth = mean(growth_rates)
    volatility = stdev(growth_rates) if len(growth_rates) > 1 else 0

    # Compare recent vs earlier growth
    mid = len(growth_rates) // 2
    recent_avg = mean(growth_rates[mid:])
    earlier_avg = mean(growth_rates[:mid])

    components = {
        "avg_growth_rate": round(avg_growth * 100, 2),
        "recent_growth": round(recent_avg * 100, 2),
        "earlier_growth": round(earlier_avg * 100, 2),
        "volatility": round(volatility * 100, 2),
        "growth_rates": [round(g * 100, 2) for g in growth_rates]
    }

    # Determine trend
    if volatility > 0.30:
        trend = Trend.VOLATILE
        interpretation = f"{metric_name}: Volatile (±{volatility*100:.0f}%)"
    elif recent_avg > earlier_avg * 1.3:
        trend = Trend.STRONG_UP
        interpretation = f"{metric_name}: Accelerating strongly"
    elif recent_avg > earlier_avg * 1.1:
        trend = Trend.UP
        interpretation = f"{metric_name}: Accelerating"
    elif recent_avg < earlier_avg * 0.7:
        trend = Trend.STRONG_DOWN
        interpretation = f"{metric_name}: Decelerating sharply"
    elif recent_avg < earlier_avg * 0.9:
        trend = Trend.DOWN
        interpretation = f"{metric_name}: Decelerating"
    else:
        trend = Trend.STABLE
        interpretation = f"{metric_name}: Stable growth"

    flags = []
    if trend in [Trend.STRONG_DOWN, Trend.DOWN]:
        flags.append(f"Growth deceleration: {earlier_avg*100:.1f}% → {recent_avg*100:.1f}%")

    return MetricResult(
        value=avg_growth * 100,
        interpretation=interpretation,
        components=components,
        flags=flags
    )


# =============================================================================
# 7. BENCHMARKING
# =============================================================================

def calculate_percentile(value: float, peer_values: List[float]) -> float:
    """Calculate percentile rank within peer group."""
    if not peer_values:
        return 50.0
    below = sum(1 for v in peer_values if v < value)
    return (below / len(peer_values)) * 100


def calculate_z_score(value: float, peer_values: List[float]) -> float:
    """Calculate z-score vs peer group."""
    if len(peer_values) < 2:
        return 0.0
    peer_mean = mean(peer_values)
    peer_std = stdev(peer_values)
    if peer_std == 0:
        return 0.0
    return (value - peer_mean) / peer_std


def benchmark_metric(
    company_value: float,
    industry_values: List[float],
    metric_name: str,
    higher_is_better: bool = True
) -> BenchmarkResult:
    """
    Compare a metric to industry peers.

    Returns percentile, z-score, and interpretation.
    """
    if not industry_values:
        return BenchmarkResult(
            raw_value=company_value,
            percentile=50.0,
            z_score=0.0,
            vs_median=0.0,
            interpretation="No peer data available"
        )

    percentile = calculate_percentile(company_value, industry_values)
    z_score = calculate_z_score(company_value, industry_values)
    industry_median = median(industry_values)
    vs_median = ((company_value - industry_median) / abs(industry_median) * 100) if industry_median != 0 else 0

    # Interpretation
    if higher_is_better:
        if percentile >= 80:
            interpretation = f"Top quintile ({percentile:.0f}th percentile)"
        elif percentile >= 60:
            interpretation = f"Above average ({percentile:.0f}th percentile)"
        elif percentile >= 40:
            interpretation = f"Average ({percentile:.0f}th percentile)"
        elif percentile >= 20:
            interpretation = f"Below average ({percentile:.0f}th percentile)"
        else:
            interpretation = f"Bottom quintile ({percentile:.0f}th percentile)"
    else:
        # Lower is better (e.g., debt ratios)
        if percentile <= 20:
            interpretation = f"Top quintile (low {metric_name})"
        elif percentile <= 40:
            interpretation = f"Above average (low {metric_name})"
        elif percentile <= 60:
            interpretation = f"Average {metric_name}"
        elif percentile <= 80:
            interpretation = f"Below average (high {metric_name})"
        else:
            interpretation = f"Bottom quintile (high {metric_name})"

    return BenchmarkResult(
        raw_value=company_value,
        percentile=round(percentile, 1),
        z_score=round(z_score, 2),
        vs_median=round(vs_median, 1),
        interpretation=interpretation
    )


# =============================================================================
# 8. COMPREHENSIVE CALCULATOR
# =============================================================================

@dataclass
class ComprehensiveAnalysis:
    """Complete analysis output for a company."""
    ticker: str

    # Composite Scores
    piotroski: Optional[MetricResult] = None
    altman_z: Optional[MetricResult] = None
    ohlson_o: Optional[MetricResult] = None
    beneish_m: Optional[MetricResult] = None
    magic_formula: Optional[MetricResult] = None
    
    # Credit Risk Metrics
    interest_coverage: Optional[MetricResult] = None
    leverage_ratio: Optional[MetricResult] = None
    refinancing_risk: Optional[MetricResult] = None
    stress_test_result: Any = None # StressTestResult from credit_metrics

    # Quality Metrics
    sloan_accrual: Optional[MetricResult] = None
    gross_profitability: Optional[MetricResult] = None
    fcf_conversion: Optional[MetricResult] = None

    # Shareholder Returns
    shareholder_yield: Optional[MetricResult] = None

    # Value Creation
    eva: Optional[MetricResult] = None
    owner_earnings: Optional[MetricResult] = None

    # Decomposition
    dupont: Optional[MetricResult] = None

    # Growth
    sustainable_growth: Optional[MetricResult] = None
    revenue_trend: Optional[MetricResult] = None
    earnings_trend: Optional[MetricResult] = None

    # Summary
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    overall_quality_score: float = 0.0  # 0-100


def aggregate_flags(analysis: ComprehensiveAnalysis) -> Tuple[List[str], List[str]]:
    """Collect all red and green flags from analysis."""
    red_flags = []
    green_flags = []

    for field_name in ['piotroski', 'altman_z', 'ohlson_o', 'beneish_m',
                       'sloan_accrual', 'fcf_conversion', 'shareholder_yield',
                       'eva', 'owner_earnings', 'dupont', 'sustainable_growth']:
        result = getattr(analysis, field_name, None)
        if result and hasattr(result, 'flags'):
            for flag in result.flags:
                if '⚠️' in flag or 'DANGER' in flag or 'HIGH' in flag or 'Negative' in flag:
                    red_flags.append(flag)
                elif 'Excellent' in flag or 'Strong' in flag or 'Top' in flag:
                    green_flags.append(flag)

    return red_flags, green_flags


def calculate_quality_score(analysis: ComprehensiveAnalysis) -> float:
    """
    Calculate overall quality score (0-100) from component metrics.

    Weights:
    - Piotroski F-Score: 15%
    - Altman Z (inverse distress): 10%
    - Beneish M (inverse manipulation): 10%
    - Gross Profitability: 15%
    - FCF Conversion: 15%
    - Shareholder Yield: 10%
    - EVA (positive/negative): 10%
    - DuPont ROE: 15%
    """
    score = 50  # Start at average

    # Piotroski (0-9 → 0-100)
    if analysis.piotroski:
        piotroski_contribution = (analysis.piotroski.value / 9) * 15
        score += piotroski_contribution - 7.5  # Center around 50

    # Altman Z (>3 is safe)
    if analysis.altman_z:
        z = analysis.altman_z.value
        if z > 3:
            score += 10
        elif z > 2:
            score += 5
        elif z < 1.8:
            score -= 10

    # Beneish M (< -2.22 is safe)
    if analysis.beneish_m:
        m = analysis.beneish_m.value
        if m < -2.22:
            score += 10
        elif m > -1.78:
            score -= 15

    # FCF Conversion (>80% is good)
    if analysis.fcf_conversion:
        if analysis.fcf_conversion.value >= 100:
            score += 15
        elif analysis.fcf_conversion.value >= 80:
            score += 10
        elif analysis.fcf_conversion.value < 50:
            score -= 10

    # Bound to 0-100
    return max(0, min(100, score))
