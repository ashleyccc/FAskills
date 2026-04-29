"""
Professional Financial Metrics Calculator

Pre-computes institutional-grade financial metrics for LLM expert analysis.
Uses established formulas from academic finance literature.

Sources:
- Piotroski F-Score: Stanford Accounting Research (2000)
- Altman Z-Score: NYU (1968)
- Beneish M-Score: Indiana University (1999)
- Owner Earnings: Warren Buffett (Berkshire Letters)
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import math


class ZScoreZone(Enum):
    SAFE = "safe"
    GREY_UPPER = "grey_upper"
    GREY_LOWER = "grey_lower"
    DISTRESS = "distress"


class GrowthTrend(Enum):
    ACCELERATING = "accelerating"
    STEADY = "steady"
    DECELERATING = "decelerating"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class PiotroskiResult:
    """Piotroski F-Score result with component breakdown."""
    f_score: int
    profitability_score: int  # 0-4
    leverage_score: int       # 0-3
    efficiency_score: int     # 0-2
    components: Dict[str, int]
    interpretation: str  # "very_strong", "strong", "average", "weak"


@dataclass
class AltmanResult:
    """Altman Z-Score result with component breakdown."""
    z_score: float
    zone: ZScoreZone
    components: Dict[str, float]
    probability_of_distress: str  # "low", "moderate", "high", "very_high"


@dataclass
class BeneishResult:
    """Beneish M-Score result for earnings manipulation detection."""
    m_score: float
    likely_manipulator: bool
    components: Dict[str, float]
    red_flags: List[str]


@dataclass
class OwnerEarningsResult:
    """Buffett's Owner Earnings calculation."""
    owners_earnings: float
    owners_earnings_conservative: float  # Using full CapEx
    components: Dict[str, float]
    per_share: float


@dataclass
class ROICResult:
    """Return on Invested Capital."""
    roic: float
    nopat: float
    invested_capital: float
    interpretation: str  # "excellent", "good", "average", "poor"


@dataclass
class GrahamValuation:
    """Graham valuation metrics."""
    graham_number: Optional[float]
    ncav_per_share: float
    ncav_conservative: float
    buy_below_graham: Optional[float]
    buy_below_ncav: float
    margin_of_safety_graham: Optional[float]
    margin_of_safety_ncav: float


@dataclass
class ValuationMetrics:
    """Standard valuation ratios."""
    pe_ratio: Optional[float]
    peg_ratio: Optional[float]
    price_to_sales: Optional[float]
    price_to_book: Optional[float]
    ev_to_ebitda: Optional[float]
    ev_to_revenue: Optional[float]
    fcf_yield: Optional[float]
    earnings_yield: Optional[float]
    dividend_yield: Optional[float]


@dataclass
class GrowthAnalysis:
    """Growth trend analysis."""
    revenue_cagr_5yr: Optional[float]
    revenue_cagr_10yr: Optional[float]
    eps_cagr_5yr: Optional[float]
    eps_cagr_10yr: Optional[float]
    revenue_trend: GrowthTrend
    eps_trend: GrowthTrend
    margin_trend: GrowthTrend
    recent_growth_rates: List[float]


# =============================================================================
# PIOTROSKI F-SCORE
# =============================================================================

def calculate_piotroski(
    # Current year
    net_income: float,
    operating_cash_flow: float,
    total_assets_begin: float,
    long_term_debt: float,
    current_assets: float,
    current_liabilities: float,
    shares_outstanding: float,
    gross_profit: float,
    revenue: float,
    # Previous year
    net_income_prev: float,
    operating_cash_flow_prev: float,
    total_assets_begin_prev: float,
    long_term_debt_prev: float,
    current_assets_prev: float,
    current_liabilities_prev: float,
    shares_outstanding_prev: float,
    gross_profit_prev: float,
    revenue_prev: float,
) -> PiotroskiResult:
    """
    Calculate Piotroski F-Score (9 criteria).

    Criteria:
    - Profitability (4): ROA > 0, CFO > 0, ΔROA > 0, CFO > ROA
    - Leverage (3): ΔLeverage < 0, ΔCurrent Ratio > 0, No equity issuance
    - Efficiency (2): ΔGross Margin > 0, ΔAsset Turnover > 0
    """
    components = {}

    # === PROFITABILITY (4 signals) ===

    # F1: ROA > 0
    roa = net_income / total_assets_begin if total_assets_begin > 0 else 0
    components['f_roa'] = 1 if roa > 0 else 0

    # F2: CFO > 0
    cfo_ratio = operating_cash_flow / total_assets_begin if total_assets_begin > 0 else 0
    components['f_cfo'] = 1 if cfo_ratio > 0 else 0

    # F3: ΔROA > 0
    roa_prev = net_income_prev / total_assets_begin_prev if total_assets_begin_prev > 0 else 0
    components['f_delta_roa'] = 1 if roa > roa_prev else 0

    # F4: Accruals (CFO/Assets > ROA)
    components['f_accrual'] = 1 if cfo_ratio > roa else 0

    profitability_score = sum([
        components['f_roa'],
        components['f_cfo'],
        components['f_delta_roa'],
        components['f_accrual']
    ])

    # === LEVERAGE / LIQUIDITY (3 signals) ===

    # F5: Decrease in leverage
    avg_assets = (total_assets_begin + total_assets_begin_prev) / 2
    avg_assets_prev = total_assets_begin_prev  # Simplified
    leverage = long_term_debt / avg_assets if avg_assets > 0 else 0
    leverage_prev = long_term_debt_prev / avg_assets_prev if avg_assets_prev > 0 else 0
    components['f_leverage'] = 1 if leverage < leverage_prev else 0

    # F6: Increase in current ratio
    current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
    current_ratio_prev = current_assets_prev / current_liabilities_prev if current_liabilities_prev > 0 else 0
    components['f_liquidity'] = 1 if current_ratio > current_ratio_prev else 0

    # F7: No equity issuance
    components['f_no_dilution'] = 1 if shares_outstanding <= shares_outstanding_prev else 0

    leverage_score = sum([
        components['f_leverage'],
        components['f_liquidity'],
        components['f_no_dilution']
    ])

    # === OPERATING EFFICIENCY (2 signals) ===

    # F8: Increase in gross margin
    gross_margin = gross_profit / revenue if revenue > 0 else 0
    gross_margin_prev = gross_profit_prev / revenue_prev if revenue_prev > 0 else 0
    components['f_gross_margin'] = 1 if gross_margin > gross_margin_prev else 0

    # F9: Increase in asset turnover
    asset_turnover = revenue / total_assets_begin if total_assets_begin > 0 else 0
    asset_turnover_prev = revenue_prev / total_assets_begin_prev if total_assets_begin_prev > 0 else 0
    components['f_asset_turnover'] = 1 if asset_turnover > asset_turnover_prev else 0

    efficiency_score = sum([
        components['f_gross_margin'],
        components['f_asset_turnover']
    ])

    # Total F-Score
    f_score = profitability_score + leverage_score + efficiency_score

    # Interpretation
    if f_score >= 8:
        interpretation = "very_strong"
    elif f_score >= 7:
        interpretation = "strong"
    elif f_score >= 4:
        interpretation = "average"
    else:
        interpretation = "weak"

    return PiotroskiResult(
        f_score=f_score,
        profitability_score=profitability_score,
        leverage_score=leverage_score,
        efficiency_score=efficiency_score,
        components=components,
        interpretation=interpretation
    )


# =============================================================================
# ALTMAN Z-SCORE
# =============================================================================

def calculate_altman_z(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    revenue: float,
    total_assets: float,
    total_liabilities: float,
    is_manufacturing: bool = True
) -> AltmanResult:
    """
    Calculate Altman Z-Score for bankruptcy prediction.

    Original formula (public manufacturing):
    Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 0.99×X5

    Non-manufacturing formula:
    Z" = 6.56×X1 + 3.26×X2 + 6.72×X3 + 1.05×X4
    """
    if total_assets == 0:
        return AltmanResult(
            z_score=0,
            zone=ZScoreZone.DISTRESS,
            components={},
            probability_of_distress="very_high"
        )

    # Component ratios
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities if total_liabilities > 0 else 0
    x5 = revenue / total_assets

    components = {
        "x1_working_capital_ratio": x1,
        "x2_retained_earnings_ratio": x2,
        "x3_ebit_ratio": x3,
        "x4_market_to_liabilities": x4,
        "x5_asset_turnover": x5
    }

    if is_manufacturing:
        z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 0.99*x5
        # Interpretation thresholds for original formula
        if z_score > 3.0:
            zone = ZScoreZone.SAFE
            prob = "low"
        elif z_score > 2.7:
            zone = ZScoreZone.GREY_UPPER
            prob = "low"
        elif z_score > 1.8:
            zone = ZScoreZone.GREY_LOWER
            prob = "moderate"
        else:
            zone = ZScoreZone.DISTRESS
            prob = "high" if z_score > 1.0 else "very_high"
    else:
        # Non-manufacturing formula (excludes asset turnover)
        z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
        # Different thresholds for Z" formula
        if z_score > 2.6:
            zone = ZScoreZone.SAFE
            prob = "low"
        elif z_score > 1.1:
            zone = ZScoreZone.GREY_LOWER
            prob = "moderate"
        else:
            zone = ZScoreZone.DISTRESS
            prob = "high"

    return AltmanResult(
        z_score=z_score,
        zone=zone,
        components=components,
        probability_of_distress=prob
    )


# =============================================================================
# BENEISH M-SCORE
# =============================================================================

def calculate_beneish_m(
    # Current year
    receivables: float,
    revenue: float,
    gross_profit: float,
    current_assets: float,
    ppe: float,
    securities: float,
    total_assets: float,
    depreciation: float,
    sga_expense: float,
    total_debt: float,
    working_capital_change: float,
    # Previous year
    receivables_prev: float,
    revenue_prev: float,
    gross_profit_prev: float,
    current_assets_prev: float,
    ppe_prev: float,
    securities_prev: float,
    total_assets_prev: float,
    depreciation_prev: float,
    sga_expense_prev: float,
    total_debt_prev: float,
) -> BeneishResult:
    """
    Calculate Beneish M-Score to detect earnings manipulation.

    M = −4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
        + 0.115×DEPI − 0.172×SGAI + 4.679×TATA − 0.327×LVGI

    M > -1.78 suggests likely earnings manipulation.
    """
    red_flags = []

    # DSRI: Days Sales in Receivables Index
    dsr = receivables / revenue if revenue > 0 else 0
    dsr_prev = receivables_prev / revenue_prev if revenue_prev > 0 else 0
    dsri = dsr / dsr_prev if dsr_prev > 0 else 1
    if dsri > 1.05:
        red_flags.append(f"DSRI={dsri:.2f}: Receivables growing faster than revenue")

    # GMI: Gross Margin Index
    gm = gross_profit / revenue if revenue > 0 else 0
    gm_prev = gross_profit_prev / revenue_prev if revenue_prev > 0 else 0
    gmi = gm_prev / gm if gm > 0 else 1
    if gmi > 1.04:
        red_flags.append(f"GMI={gmi:.2f}: Deteriorating gross margins")

    # AQI: Asset Quality Index
    hard_assets = current_assets + ppe + securities
    aq = 1 - (hard_assets / total_assets) if total_assets > 0 else 0
    hard_assets_prev = current_assets_prev + ppe_prev + securities_prev
    aq_prev = 1 - (hard_assets_prev / total_assets_prev) if total_assets_prev > 0 else 0
    aqi = aq / aq_prev if aq_prev > 0 else 1
    if aqi > 1.0:
        red_flags.append(f"AQI={aqi:.2f}: Increasing soft assets (possible cost deferral)")

    # SGI: Sales Growth Index
    sgi = revenue / revenue_prev if revenue_prev > 0 else 1
    if sgi > 1.5:
        red_flags.append(f"SGI={sgi:.2f}: Very high sales growth (scrutinize quality)")

    # DEPI: Depreciation Index
    dep_rate = depreciation / (depreciation + ppe) if (depreciation + ppe) > 0 else 0
    dep_rate_prev = depreciation_prev / (depreciation_prev + ppe_prev) if (depreciation_prev + ppe_prev) > 0 else 0
    depi = dep_rate_prev / dep_rate if dep_rate > 0 else 1
    if depi > 1.05:
        red_flags.append(f"DEPI={depi:.2f}: Slowing depreciation (extending asset lives)")

    # SGAI: SGA Index
    sga_ratio = sga_expense / revenue if revenue > 0 else 0
    sga_ratio_prev = sga_expense_prev / revenue_prev if revenue_prev > 0 else 0
    sgai = sga_ratio / sga_ratio_prev if sga_ratio_prev > 0 else 1

    # LVGI: Leverage Index
    lev = total_debt / total_assets if total_assets > 0 else 0
    lev_prev = total_debt_prev / total_assets_prev if total_assets_prev > 0 else 0
    lvgi = lev / lev_prev if lev_prev > 0 else 1

    # TATA: Total Accruals to Total Assets
    tata = (working_capital_change - depreciation) / total_assets if total_assets > 0 else 0
    if tata > 0.05:
        red_flags.append(f"TATA={tata:.2f}: High accruals relative to assets")

    # Calculate M-Score
    m_score = (
        -4.84
        + 0.92 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )

    components = {
        "dsri": dsri,
        "gmi": gmi,
        "aqi": aqi,
        "sgi": sgi,
        "depi": depi,
        "sgai": sgai,
        "lvgi": lvgi,
        "tata": tata
    }

    return BeneishResult(
        m_score=m_score,
        likely_manipulator=m_score > -1.78,
        components=components,
        red_flags=red_flags
    )


# =============================================================================
# OWNER EARNINGS (BUFFETT)
# =============================================================================

def calculate_owner_earnings(
    net_income: float,
    depreciation: float,
    amortization: float,
    other_noncash_charges: float,
    capex: float,
    revenue: float,
    revenue_prev: float,
    avg_ppe_to_revenue_7yr: float,
    shares_outstanding: float
) -> OwnerEarningsResult:
    """
    Calculate Buffett's Owner Earnings.

    Owner Earnings = Net Income + Non-Cash Charges - Maintenance CapEx

    Uses Greenwald method to estimate maintenance CapEx:
    - Calculate average PPE/Revenue ratio over 7 years
    - Growth CapEx = Ratio × Revenue Growth
    - Maintenance CapEx = Total CapEx - Growth CapEx
    """
    non_cash_charges = depreciation + amortization + other_noncash_charges

    # Greenwald method for maintenance CapEx
    revenue_growth = max(0, revenue - revenue_prev)
    growth_capex = avg_ppe_to_revenue_7yr * revenue_growth
    maintenance_capex_estimate = capex - growth_capex

    # Conservative floor: at least 50% of capex is maintenance
    maintenance_capex = max(maintenance_capex_estimate, capex * 0.5)

    owners_earnings = net_income + non_cash_charges - maintenance_capex
    owners_earnings_conservative = net_income + non_cash_charges - capex

    return OwnerEarningsResult(
        owners_earnings=owners_earnings,
        owners_earnings_conservative=owners_earnings_conservative,
        components={
            "net_income": net_income,
            "non_cash_charges": non_cash_charges,
            "total_capex": capex,
            "maintenance_capex_est": maintenance_capex,
            "growth_capex_est": growth_capex
        },
        per_share=owners_earnings / shares_outstanding if shares_outstanding > 0 else 0
    )


# =============================================================================
# ROIC (RETURN ON INVESTED CAPITAL)
# =============================================================================

def calculate_roic(
    ebit: float,
    tax_rate: float,
    total_equity: float,
    total_debt: float,
    cash: float,
    total_equity_prev: float,
    total_debt_prev: float,
    cash_prev: float
) -> ROICResult:
    """
    Calculate Return on Invested Capital.

    ROIC = NOPAT / Average Invested Capital
    NOPAT = EBIT × (1 - Tax Rate)
    Invested Capital = Equity + Debt - Cash
    """
    nopat = ebit * (1 - tax_rate)

    ic_current = total_equity + total_debt - cash
    ic_prev = total_equity_prev + total_debt_prev - cash_prev
    avg_invested_capital = (ic_current + ic_prev) / 2

    roic = nopat / avg_invested_capital if avg_invested_capital > 0 else 0

    if roic > 0.20:
        interpretation = "excellent"
    elif roic > 0.15:
        interpretation = "good"
    elif roic > 0.10:
        interpretation = "average"
    else:
        interpretation = "poor"

    return ROICResult(
        roic=roic,
        nopat=nopat,
        invested_capital=avg_invested_capital,
        interpretation=interpretation
    )


# =============================================================================
# GRAHAM VALUATION
# =============================================================================

def calculate_graham_valuation(
    eps: float,
    book_value_per_share: float,
    current_assets: float,
    total_liabilities: float,
    preferred_stock: float,
    shares_outstanding: float,
    cash: float,
    receivables: float,
    inventory: float,
    current_price: float
) -> GrahamValuation:
    """
    Calculate Graham valuation metrics.

    Graham Number = √(22.5 × EPS × BVPS)
    NCAV = (Current Assets - Total Liabilities) / Shares
    Conservative NCAV = (Cash + 0.75×Receivables + 0.5×Inventory - Liabilities) / Shares
    """
    # Graham Number
    if eps > 0 and book_value_per_share > 0:
        graham_number = math.sqrt(22.5 * eps * book_value_per_share)
        buy_below_graham = graham_number
        margin_of_safety_graham = (graham_number - current_price) / graham_number if graham_number > 0 else None
    else:
        graham_number = None
        buy_below_graham = None
        margin_of_safety_graham = None

    # Standard NCAV
    ncav = current_assets - total_liabilities - preferred_stock
    ncav_per_share = ncav / shares_outstanding if shares_outstanding > 0 else 0
    buy_below_ncav = ncav_per_share * 0.67  # Graham's 2/3 rule

    # Conservative NCAV (liquidation values)
    adjusted_assets = cash + (0.75 * receivables) + (0.5 * inventory)
    ncav_conservative = (adjusted_assets - total_liabilities - preferred_stock) / shares_outstanding if shares_outstanding > 0 else 0

    margin_of_safety_ncav = (ncav_per_share - current_price) / ncav_per_share if ncav_per_share > 0 else 0

    return GrahamValuation(
        graham_number=graham_number,
        ncav_per_share=ncav_per_share,
        ncav_conservative=ncav_conservative,
        buy_below_graham=buy_below_graham,
        buy_below_ncav=buy_below_ncav,
        margin_of_safety_graham=margin_of_safety_graham,
        margin_of_safety_ncav=margin_of_safety_ncav
    )


# =============================================================================
# VALUATION METRICS
# =============================================================================

def calculate_valuation_metrics(
    price: float,
    eps: float,
    eps_growth_rate: float,
    book_value_per_share: float,
    revenue: float,
    ebitda: float,
    fcf: float,
    dividends_per_share: float,
    shares_outstanding: float,
    total_debt: float,
    cash: float
) -> ValuationMetrics:
    """Calculate standard valuation ratios."""
    market_cap = price * shares_outstanding
    enterprise_value = market_cap + total_debt - cash

    return ValuationMetrics(
        pe_ratio=price / eps if eps > 0 else None,
        peg_ratio=(price / eps) / (eps_growth_rate * 100) if eps > 0 and eps_growth_rate > 0 else None,
        price_to_sales=market_cap / revenue if revenue > 0 else None,
        price_to_book=price / book_value_per_share if book_value_per_share > 0 else None,
        ev_to_ebitda=enterprise_value / ebitda if ebitda > 0 else None,
        ev_to_revenue=enterprise_value / revenue if revenue > 0 else None,
        fcf_yield=(fcf / market_cap) * 100 if market_cap > 0 else None,
        earnings_yield=(eps / price) * 100 if price > 0 else None,
        dividend_yield=(dividends_per_share / price) * 100 if price > 0 else None
    )


# =============================================================================
# GROWTH ANALYSIS
# =============================================================================

def calculate_cagr(beginning_value: float, ending_value: float, years: int) -> Optional[float]:
    """Calculate Compound Annual Growth Rate."""
    if beginning_value <= 0 or ending_value <= 0 or years <= 0:
        return None
    return (ending_value / beginning_value) ** (1 / years) - 1


def analyze_growth_trend(values: List[float]) -> GrowthTrend:
    """
    Analyze growth trajectory.

    Returns: accelerating, decelerating, steady, volatile, insufficient_data
    """
    if len(values) < 3:
        return GrowthTrend.INSUFFICIENT_DATA

    # Calculate year-over-year growth rates
    growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] != 0:
            growth_rates.append((values[i] - values[i-1]) / abs(values[i-1]))

    if len(growth_rates) < 2:
        return GrowthTrend.INSUFFICIENT_DATA

    # Calculate volatility
    avg_growth = sum(growth_rates) / len(growth_rates)
    variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
    volatility = variance ** 0.5

    # Check recent vs earlier growth
    recent_count = min(3, len(growth_rates))
    earlier_count = min(3, len(growth_rates) - recent_count)

    recent_avg = sum(growth_rates[-recent_count:]) / recent_count
    earlier_avg = sum(growth_rates[:earlier_count]) / earlier_count if earlier_count > 0 else growth_rates[0]

    # Determine trend
    if volatility > 0.3:
        return GrowthTrend.VOLATILE
    elif recent_avg > earlier_avg * 1.2:
        return GrowthTrend.ACCELERATING
    elif recent_avg < earlier_avg * 0.8:
        return GrowthTrend.DECELERATING
    else:
        return GrowthTrend.STEADY


def calculate_growth_analysis(
    revenues: List[float],
    eps_values: List[float],
    margins: List[float]
) -> GrowthAnalysis:
    """Comprehensive growth analysis."""
    # Revenue CAGRs
    rev_cagr_5yr = calculate_cagr(revenues[-6], revenues[-1], 5) if len(revenues) >= 6 else None
    rev_cagr_10yr = calculate_cagr(revenues[-11], revenues[-1], 10) if len(revenues) >= 11 else None

    # EPS CAGRs
    eps_cagr_5yr = calculate_cagr(eps_values[-6], eps_values[-1], 5) if len(eps_values) >= 6 else None
    eps_cagr_10yr = calculate_cagr(eps_values[-11], eps_values[-1], 10) if len(eps_values) >= 11 else None

    # Trends
    rev_trend = analyze_growth_trend(revenues)
    eps_trend = analyze_growth_trend(eps_values)
    margin_trend = analyze_growth_trend(margins)

    # Recent growth rates
    recent_growth = []
    for i in range(1, min(6, len(revenues))):
        if revenues[-(i+1)] != 0:
            recent_growth.append((revenues[-i] - revenues[-(i+1)]) / abs(revenues[-(i+1)]))

    return GrowthAnalysis(
        revenue_cagr_5yr=rev_cagr_5yr,
        revenue_cagr_10yr=rev_cagr_10yr,
        eps_cagr_5yr=eps_cagr_5yr,
        eps_cagr_10yr=eps_cagr_10yr,
        revenue_trend=rev_trend,
        eps_trend=eps_trend,
        margin_trend=margin_trend,
        recent_growth_rates=recent_growth
    )


# =============================================================================
# COMPREHENSIVE ANALYSIS
# =============================================================================

@dataclass
class ComprehensiveMetrics:
    """All calculated metrics for a company."""
    ticker: str
    piotroski: Optional[PiotroskiResult]
    altman: Optional[AltmanResult]
    beneish: Optional[BeneishResult]
    owner_earnings: Optional[OwnerEarningsResult]
    roic: Optional[ROICResult]
    graham: Optional[GrahamValuation]
    valuation: Optional[ValuationMetrics]
    growth: Optional[GrowthAnalysis]
    data_quality: Dict[str, bool]  # Which metrics had complete data


def calculate_all_metrics(
    ticker: str,
    financials: Dict[str, Any],
    market_data: Dict[str, Any]
) -> ComprehensiveMetrics:
    """
    Calculate all professional metrics from raw financial data.

    Args:
        ticker: Stock ticker symbol
        financials: Dict containing income_statements, balance_sheets, cash_flows
        market_data: Dict containing price, market_cap, shares_outstanding
    """
    data_quality = {}

    # Extract current and previous year data
    # (Implementation would parse the actual API response structure)

    # For now, return a template showing the structure
    return ComprehensiveMetrics(
        ticker=ticker,
        piotroski=None,
        altman=None,
        beneish=None,
        owner_earnings=None,
        roic=None,
        graham=None,
        valuation=None,
        growth=None,
        data_quality=data_quality
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format a decimal as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_currency(value: Optional[float], decimals: int = 0) -> str:
    """Format a number as currency."""
    if value is None:
        return "N/A"
    if abs(value) >= 1e12:
        return f"${value/1e12:.{decimals}f}T"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.{decimals}f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.{decimals}f}M"
    else:
        return f"${value:,.{decimals}f}"


def interpret_score(metric_name: str, value: float) -> str:
    """Provide human-readable interpretation of a score."""
    interpretations = {
        "piotroski": {
            (8, 10): "Very Strong - Excellent financial health",
            (7, 8): "Strong - Good financial position",
            (4, 7): "Average - Mixed signals",
            (0, 4): "Weak - Concerning financial health"
        },
        "altman_z": {
            (3.0, float('inf')): "Safe Zone - Low bankruptcy risk",
            (2.7, 3.0): "Grey Zone (Upper) - Probably safe",
            (1.8, 2.7): "Grey Zone (Lower) - Caution advised",
            (float('-inf'), 1.8): "Distress Zone - High bankruptcy risk"
        },
        "beneish_m": {
            (float('-inf'), -2.22): "Very Unlikely Manipulator",
            (-2.22, -1.78): "Unlikely Manipulator",
            (-1.78, float('inf')): "Likely Manipulator - Investigate further"
        }
    }

    if metric_name not in interpretations:
        return "No interpretation available"

    for (low, high), interpretation in interpretations[metric_name].items():
        if low <= value < high:
            return interpretation

    return "Value out of expected range"
