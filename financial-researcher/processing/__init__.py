"""
Financial Researcher - Python Processing Layer

Pre-calculates professional financial metrics for LLM expert analysis.

USAGE:
    from processing import run_analysis, AnalysisResult

    result = run_analysis(
        ticker="AAPL",
        income_statements=[...],
        balance_sheets=[...],
        cash_flows=[...],
        metrics={...},
        price_data={...},
    )

    # Get formatted context for LLM
    context = result.to_llm_context()

    # Get expert-specific context
    buffett_context = format_for_expert(result, "buffett")

METRICS CALCULATED (not provided by API):
    Composite Scores:
    - Piotroski F-Score (9 criteria)
    - Altman Z-Score (5 ratios) - bankruptcy prediction
    - Ohlson O-Score (9 factors) - bankruptcy probability
    - Beneish M-Score (8 variables) - earnings manipulation detection
    - Magic Formula (Greenblatt)

    Quality Metrics:
    - Sloan Accrual Ratio - earnings quality
    - Gross Profitability (Novy-Marx)
    - FCF Conversion Ratio

    Value Creation:
    - Owner Earnings (Buffett)
    - Economic Value Added (EVA)

    Decomposition:
    - DuPont 5-Factor ROE Analysis

    Growth:
    - Sustainable Growth Rate
    - Trend Analysis (accelerating/decelerating)

    Shareholder Returns:
    - Total Shareholder Yield (dividend + buyback + debt paydown)

    Benchmarking:
    - Industry percentiles
    - Z-scores vs peers

METRICS FROM API (don't recalculate):
    - ROIC, ROE, ROA
    - P/E, P/B, P/S, EV/EBITDA, PEG
    - Profit margins (gross, operating, net)
    - Liquidity ratios (current, quick)
    - Leverage ratios (D/E, interest coverage)
    - Growth rates (revenue, EPS, FCF)
    - Efficiency ratios (asset turnover, DSO)
"""

# Main entry point
from .orchestrator import (
    run_analysis,
    calculate_all_metrics,
    format_for_expert,
    AnalysisResult,
)

# Data extraction
from .data_extractor import (
    CompanyData,
    FinancialData,
    MetricsData,
    PriceData,
    HoldingsData,
    InsiderData,
    extract_company_data,
    get_current_and_previous,
)

# Metric calculators
from .metrics_calculator import (
    # Result types
    MetricResult,
    BenchmarkResult,
    ComprehensiveAnalysis,
    ScoreInterpretation,
    Trend,

    # Composite scores
    piotroski_f_score,
    altman_z_score,
    ohlson_o_score,
    beneish_m_score,
    magic_formula_rank,

    # Quality metrics
    sloan_accrual_ratio,
    gross_profitability,
    fcf_conversion,

    # Shareholder returns
    shareholder_yield,

    # Value creation
    economic_value_added,
    owner_earnings,

    # Decomposition
    dupont_5_factor,

    # Growth
    sustainable_growth_rate,
    analyze_trend,

    # Benchmarking
    benchmark_metric,
    calculate_percentile,
    calculate_z_score,

    # Summary functions
    aggregate_flags,
    calculate_quality_score,
)

from .credit_metrics import (
    calculate_icr,
    calculate_leverage,
    calculate_refinancing_risk,
    run_recession_stress_test,
    CreditMetricResult,
    StressTestResult,
)

# Legacy exports from financial_metrics.py (for backwards compatibility)
from .financial_metrics import (
    PiotroskiResult,
    AltmanResult,
    BeneishResult,
    OwnerEarningsResult,
    ROICResult,
    GrahamValuation,
    ValuationMetrics,
    GrowthAnalysis,
    ComprehensiveMetrics,
    ZScoreZone,
    GrowthTrend,
    calculate_piotroski,
    calculate_altman_z,
    calculate_beneish_m,
    calculate_owner_earnings,
    calculate_roic,
    calculate_graham_valuation,
    calculate_valuation_metrics,
    calculate_cagr,
    analyze_growth_trend,
    calculate_growth_analysis,
    calculate_all_metrics as calculate_all_metrics_legacy,
    format_percentage,
    format_currency,
    interpret_score,
)

__version__ = "2.0.0"

__all__ = [
    # Main entry point
    "run_analysis",
    "calculate_all_metrics",
    "format_for_expert",
    "AnalysisResult",

    # Data classes
    "CompanyData",
    "FinancialData",
    "MetricsData",
    "PriceData",
    "HoldingsData",
    "InsiderData",
    "MetricResult",
    "BenchmarkResult",
    "ComprehensiveAnalysis",

    # Enums
    "ScoreInterpretation",
    "Trend",

    # Extraction
    "extract_company_data",
    "get_current_and_previous",

    # Composite scores
    "piotroski_f_score",
    "altman_z_score",
    "ohlson_o_score",
    "beneish_m_score",
    "magic_formula_rank",

    # Quality
    "sloan_accrual_ratio",
    "gross_profitability",
    "fcf_conversion",

    # Shareholder returns
    "shareholder_yield",

    # Value creation
    "economic_value_added",
    "owner_earnings",

    # Decomposition
    "dupont_5_factor",

    # Growth
    "sustainable_growth_rate",
    "analyze_trend",

    # Benchmarking
    "benchmark_metric",
    "calculate_percentile",
    "calculate_z_score",

    # Summary
    "aggregate_flags",
    "calculate_quality_score",

    # Credit Metrics
    "calculate_icr",
    "calculate_leverage",
    "calculate_refinancing_risk",
    "run_recession_stress_test",
    "CreditMetricResult",
    "StressTestResult",

    # Legacy (backwards compatibility)
    "PiotroskiResult",
    "AltmanResult",
    "BeneishResult",
    "OwnerEarningsResult",
    "ROICResult",
    "GrahamValuation",
    "ValuationMetrics",
    "GrowthAnalysis",
    "ComprehensiveMetrics",
    "ZScoreZone",
    "GrowthTrend",
    "format_percentage",
    "format_currency",
    "interpret_score",
]
