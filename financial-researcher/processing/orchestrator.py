"""
Financial Metrics Orchestrator

Ties together data extraction and metric calculation into a single pipeline.
Produces a structured analysis output ready for LLM expert consumption.

Usage:
    from processing import run_analysis

    result = run_analysis(
        ticker="AAPL",
        income_statements=[...],
        balance_sheets=[...],
        cash_flows=[...],
        metrics={...},
        price_data={...},
    )
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

from .data_extractor import (
    CompanyData,
    FinancialData,
    extract_company_data,
    get_current_and_previous,
)
from .metrics_calculator import (
    MetricResult,
    BenchmarkResult,
    ComprehensiveAnalysis,
    piotroski_f_score,
    altman_z_score,
    ohlson_o_score,
    beneish_m_score,
    magic_formula_rank,
    sloan_accrual_ratio,
    gross_profitability,
    fcf_conversion,
    shareholder_yield,
    economic_value_added,
    owner_earnings,
    dupont_5_factor,
    sustainable_growth_rate,
    analyze_trend,
    benchmark_metric,
    aggregate_flags,
    calculate_quality_score,
)
from .credit_metrics import (
    calculate_icr,
    calculate_leverage,
    calculate_refinancing_risk,
    run_recession_stress_test,
)


@dataclass
class AnalysisResult:
    """Complete analysis output for LLM consumption."""
    ticker: str
    company_name: str
    analysis_date: str

    # Raw company data
    company_data: CompanyData = None

    # Calculated metrics
    comprehensive_analysis: ComprehensiveAnalysis = None

    # Summary for quick reference
    summary: Dict[str, Any] = field(default_factory=dict)

    # Data quality notes
    data_quality_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "analysis_date": self.analysis_date,
            "summary": self.summary,
            "data_quality_notes": self.data_quality_notes,
        }

    def to_llm_context(self) -> str:
        """Format as context string for LLM experts."""
        lines = [
            f"# Pre-Calculated Metrics for {self.ticker}",
            f"Company: {self.company_name}",
            f"Analysis Date: {self.analysis_date}",
            "",
            "## Composite Scores",
        ]

        if self.comprehensive_analysis:
            ca = self.comprehensive_analysis

            # Piotroski
            if ca.piotroski:
                lines.append(f"### Piotroski F-Score: {ca.piotroski.value}/9")
                lines.append(f"Interpretation: {ca.piotroski.interpretation}")
                if ca.piotroski.flags:
                    lines.append(f"Flags: {', '.join(ca.piotroski.flags)}")
                lines.append("")

            # Altman Z
            if ca.altman_z:
                lines.append(f"### Altman Z-Score: {ca.altman_z.value}")
                lines.append(f"Interpretation: {ca.altman_z.interpretation}")
                if ca.altman_z.flags:
                    lines.append(f"Flags: {', '.join(ca.altman_z.flags)}")
                lines.append("")

            # Beneish M
            if ca.beneish_m:
                lines.append(f"### Beneish M-Score: {ca.beneish_m.value}")
                lines.append(f"Interpretation: {ca.beneish_m.interpretation}")
                if ca.beneish_m.flags:
                    lines.append(f"Flags: {', '.join(ca.beneish_m.flags)}")
                lines.append("")

            # Ohlson O
            if ca.ohlson_o:
                lines.append(f"### Ohlson O-Score (Bankruptcy Probability): {ca.ohlson_o.value}")
                lines.append(f"Interpretation: {ca.ohlson_o.interpretation}")
                lines.append("")

            # Quality Metrics
            lines.append("## Quality Metrics")

            if ca.sloan_accrual:
                lines.append(f"### Sloan Accrual Ratio: {ca.sloan_accrual.value}%")
                lines.append(f"Interpretation: {ca.sloan_accrual.interpretation}")
                lines.append("")

            if ca.fcf_conversion:
                lines.append(f"### FCF Conversion: {ca.fcf_conversion.value}%")
                lines.append(f"Interpretation: {ca.fcf_conversion.interpretation}")
                lines.append("")

            if ca.gross_profitability:
                lines.append(f"### Gross Profitability (GP/Assets): {ca.gross_profitability.value}%")
                lines.append(f"Interpretation: {ca.gross_profitability.interpretation}")
                lines.append("")

            # Value Creation
            lines.append("## Value Creation")

            if ca.owner_earnings:
                lines.append(f"### Owner Earnings: ${ca.owner_earnings.value:,.0f}")
                lines.append(f"Interpretation: {ca.owner_earnings.interpretation}")
                lines.append("")

            if ca.eva:
                lines.append(f"### Economic Value Added (EVA): ${ca.eva.value:,.0f}")
                lines.append(f"Interpretation: {ca.eva.interpretation}")
                lines.append("")

            # Shareholder Returns
            if ca.shareholder_yield:
                lines.append("## Shareholder Returns")
                lines.append(f"### Total Shareholder Yield: {ca.shareholder_yield.value}%")
                lines.append(f"Interpretation: {ca.shareholder_yield.interpretation}")
                if ca.shareholder_yield.components:
                    comp = ca.shareholder_yield.components
                    lines.append(f"  - Dividend Yield: {comp.get('dividend_yield', 'N/A')}%")
                    lines.append(f"  - Buyback Yield: {comp.get('buyback_yield', 'N/A')}%")
                    lines.append(f"  - Debt Paydown Yield: {comp.get('debt_paydown_yield', 'N/A')}%")
                lines.append("")

            # DuPont Analysis
            if ca.dupont:
                lines.append("## ROE Decomposition (DuPont 5-Factor)")
                lines.append(f"ROE: {ca.dupont.value}%")
                lines.append(f"Analysis: {ca.dupont.interpretation}")
                if ca.dupont.components:
                    comp = ca.dupont.components
                    lines.append(f"  - Tax Burden: {comp.get('tax_burden', 'N/A')}")
                    lines.append(f"  - Interest Burden: {comp.get('interest_burden', 'N/A')}")
                    lines.append(f"  - EBIT Margin: {comp.get('ebit_margin', 'N/A')}%")
                    lines.append(f"  - Asset Turnover: {comp.get('asset_turnover', 'N/A')}")
                    lines.append(f"  - Leverage: {comp.get('leverage', 'N/A')}x")
                lines.append("")

            # Growth
            if ca.sustainable_growth:
                lines.append("## Sustainable Growth")
                lines.append(f"Sustainable Growth Rate: {ca.sustainable_growth.value}%")
                lines.append(f"Interpretation: {ca.sustainable_growth.interpretation}")
                lines.append("")

            # Red/Green Flags
            if ca.red_flags:
                lines.append("## ⚠️ RED FLAGS")
                for flag in ca.red_flags:
                    lines.append(f"- {flag}")
                lines.append("")

            if ca.green_flags:
                lines.append("## ✓ GREEN FLAGS")
                for flag in ca.green_flags:
                    lines.append(f"- {flag}")
                lines.append("")

            # Overall Quality
            lines.append(f"## Overall Quality Score: {ca.overall_quality_score}/100")

            # Credit Risk Section
            lines.append("")
            lines.append("## Credit Risk Analysis (CRO View)")
            
            if ca.interest_coverage:
                lines.append(f"### Interest Coverage Ratio: {ca.interest_coverage.value}x")
                lines.append(f"Interpretation: {ca.interest_coverage.interpretation}")
                if ca.interest_coverage.flags:
                    lines.append(f"Flags: {', '.join(ca.interest_coverage.flags)}")
                lines.append("")

            if ca.leverage_ratio:
                lines.append(f"### Leverage (Net Debt/EBITDA): {ca.leverage_ratio.value}x")
                lines.append(f"Interpretation: {ca.leverage_ratio.interpretation}")
                if ca.leverage_ratio.flags:
                    lines.append(f"Flags: {', '.join(ca.leverage_ratio.flags)}")
                lines.append("")

            if ca.refinancing_risk:
                lines.append(f"### Refinancing Risk Indicator: {ca.refinancing_risk.value}")
                lines.append(f"Interpretation: {ca.refinancing_risk.interpretation}")
                if ca.refinancing_risk.flags:
                    lines.append(f"Flags: {', '.join(ca.refinancing_risk.flags)}")
                lines.append("")

            if ca.stress_test_result:
                st = ca.stress_test_result
                lines.append(f"### Stress Test: {st.scenario_name}")
                lines.append(f"Stressed ICR: {st.stressed_icr}x (Change: {st.icr_change}x)")
                lines.append(f"Survival Check: {'PASSED' if st.survives else 'FAILED'}")
                lines.append("")

        return "\n".join(lines)


def calculate_all_metrics(company: CompanyData, wacc: float = 0.10) -> ComprehensiveAnalysis:
    """
    Calculate all professional metrics from extracted company data.

    Args:
        company: Extracted CompanyData object
        wacc: Weighted average cost of capital (default 10%)

    Returns:
        ComprehensiveAnalysis with all calculated metrics
    """
    analysis = ComprehensiveAnalysis(ticker=company.ticker)

    # Get current and previous year data
    current, previous = get_current_and_previous(company.financials_annual)

    if current.fiscal_year == 0:
        return analysis  # No data available

    # === COMPOSITE SCORES ===

    # Piotroski F-Score
    try:
        analysis.piotroski = piotroski_f_score(
            net_income=current.net_income,
            operating_cash_flow=current.operating_cash_flow,
            total_assets=current.total_assets,
            long_term_debt=current.long_term_debt,
            current_assets=current.current_assets,
            current_liabilities=current.current_liabilities,
            shares_outstanding=current.shares_outstanding,
            gross_profit=current.gross_profit,
            revenue=current.revenue,
            net_income_prev=previous.net_income,
            total_assets_prev=previous.total_assets,
            long_term_debt_prev=previous.long_term_debt,
            current_assets_prev=previous.current_assets,
            current_liabilities_prev=previous.current_liabilities,
            shares_outstanding_prev=previous.shares_outstanding,
            gross_profit_prev=previous.gross_profit,
            revenue_prev=previous.revenue,
        )
    except Exception:
        pass

    # Altman Z-Score
    try:
        # Determine if manufacturing based on sector
        is_manufacturing = company.sector.lower() in ['industrials', 'materials', 'manufacturing']

        analysis.altman_z = altman_z_score(
            working_capital=current.working_capital,
            retained_earnings=current.retained_earnings,
            ebit=current.ebit,
            market_cap=company.price.market_cap,
            revenue=current.revenue,
            total_assets=current.total_assets,
            total_liabilities=current.total_liabilities,
            is_manufacturing=is_manufacturing,
        )
    except Exception:
        pass

    # Ohlson O-Score
    try:
        analysis.ohlson_o = ohlson_o_score(
            total_assets=current.total_assets,
            total_liabilities=current.total_liabilities,
            working_capital=current.working_capital,
            current_liabilities=current.current_liabilities,
            net_income=current.net_income,
            funds_from_operations=current.operating_cash_flow,
            net_income_prev=previous.net_income,
            total_liabilities_prev=previous.total_liabilities,
        )
    except Exception:
        pass

    # Beneish M-Score
    try:
        analysis.beneish_m = beneish_m_score(
            receivables=current.accounts_receivable,
            revenue=current.revenue,
            gross_profit=current.gross_profit,
            total_assets=current.total_assets,
            ppe=current.ppe_net,
            depreciation=current.depreciation,
            sga=current.sga_expense,
            total_debt=current.total_debt,
            current_assets=current.current_assets,
            current_liabilities=current.current_liabilities,
            receivables_prev=previous.accounts_receivable,
            revenue_prev=previous.revenue,
            gross_profit_prev=previous.gross_profit,
            total_assets_prev=previous.total_assets,
            ppe_prev=previous.ppe_net,
            depreciation_prev=previous.depreciation,
            sga_prev=previous.sga_expense,
            total_debt_prev=previous.total_debt,
            net_income=current.net_income,
            operating_cash_flow=current.operating_cash_flow,
        )
    except Exception:
        pass

    # Magic Formula
    try:
        ev = company.price.market_cap + current.total_debt - current.cash
        analysis.magic_formula = magic_formula_rank(
            ebit=current.ebit,
            enterprise_value=ev,
            total_equity=current.shareholders_equity,
            total_debt=current.total_debt,
            cash=current.cash,
            ppe_net=current.ppe_net,
            working_capital=current.working_capital,
        )
    except Exception:
        pass

    # === CREDIT RISK METRICS ===
    try:
        analysis.interest_coverage = calculate_icr(
            ebit=current.ebit,
            interest_expense=current.interest_expense
        )
        
        analysis.leverage_ratio = calculate_leverage(
            net_debt=current.total_debt - current.cash,
            ebitda=current.ebitda
        )
        
        analysis.refinancing_risk = calculate_refinancing_risk(
            short_term_debt=current.short_term_debt,
            cash_and_equivalents=current.cash,
            operating_cash_flow=current.operating_cash_flow
        )
        
        analysis.stress_test_result = run_recession_stress_test(
            ebit=current.ebit,
            interest_expense=current.interest_expense,
            revenue=current.revenue
        )
    except Exception:
        pass

    # === QUALITY METRICS ===

    # Sloan Accrual Ratio
    try:
        analysis.sloan_accrual = sloan_accrual_ratio(
            net_income=current.net_income,
            operating_cash_flow=current.operating_cash_flow,
            total_assets=current.total_assets,
            total_assets_prev=previous.total_assets,
        )
    except Exception:
        pass

    # Gross Profitability
    try:
        analysis.gross_profitability = gross_profitability(
            gross_profit=current.gross_profit,
            total_assets=current.total_assets,
        )
    except Exception:
        pass

    # FCF Conversion
    try:
        analysis.fcf_conversion = fcf_conversion(
            free_cash_flow=current.free_cash_flow,
            ebitda=current.ebitda,
            net_income=current.net_income,
        )
    except Exception:
        pass

    # === SHAREHOLDER RETURNS ===

    try:
        analysis.shareholder_yield = shareholder_yield(
            dividends_paid=current.dividends_paid,
            shares_repurchased=current.shares_repurchased,
            shares_issued=current.shares_issued,
            debt_repaid=current.debt_repaid,
            market_cap=company.price.market_cap,
        )
    except Exception:
        pass

    # === VALUE CREATION ===

    # Owner Earnings
    try:
        wc_change = current.working_capital - previous.working_capital
        analysis.owner_earnings = owner_earnings(
            net_income=current.net_income,
            depreciation=current.depreciation,
            amortization=current.amortization if hasattr(current, 'amortization') else 0,
            capex=current.capex,
            working_capital_change=wc_change,
            shares_outstanding=current.shares_outstanding,
        )
    except Exception:
        pass

    # EVA
    try:
        tax_rate = current.income_tax / current.ebt if current.ebt != 0 else 0.25
        nopat = current.ebit * (1 - tax_rate)
        invested_capital = current.shareholders_equity + current.total_debt - current.cash

        analysis.eva = economic_value_added(
            nopat=nopat,
            invested_capital=invested_capital,
            wacc=wacc,
        )
    except Exception:
        pass

    # === DECOMPOSITION ===

    # DuPont 5-Factor
    try:
        analysis.dupont = dupont_5_factor(
            net_income=current.net_income,
            ebt=current.ebt,
            ebit=current.ebit,
            revenue=current.revenue,
            total_assets=current.total_assets,
            shareholders_equity=current.shareholders_equity,
        )
    except Exception:
        pass

    # === GROWTH ===

    # Sustainable Growth Rate
    try:
        roe = current.net_income / current.shareholders_equity if current.shareholders_equity > 0 else 0
        payout = abs(current.dividends_paid) / current.net_income if current.net_income > 0 else 0

        analysis.sustainable_growth = sustainable_growth_rate(
            roe=roe,
            dividend_payout_ratio=payout,
        )
    except Exception:
        pass

    # Revenue Trend
    if len(company.financials_annual) >= 3:
        revenues = [f.revenue for f in reversed(company.financials_annual)]
        analysis.revenue_trend = analyze_trend(revenues, "Revenue")

        earnings = [f.net_income for f in reversed(company.financials_annual)]
        analysis.earnings_trend = analyze_trend(earnings, "Earnings")

    # === SUMMARY ===

    # Aggregate flags
    analysis.red_flags, analysis.green_flags = aggregate_flags(analysis)

    # Calculate overall quality score
    analysis.overall_quality_score = calculate_quality_score(analysis)

    return analysis


def run_analysis(
    ticker: str,
    income_statements: List[Dict[str, Any]],
    balance_sheets: List[Dict[str, Any]],
    cash_flows: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    price_data: Dict[str, Any],
    holdings_by_investor: Dict[str, List[Dict[str, Any]]] = None,
    insider_trades: List[Dict[str, Any]] = None,
    analyst_estimates: List[Dict[str, Any]] = None,
    company_facts: Dict[str, Any] = None,
    wacc: float = 0.10,
) -> AnalysisResult:
    """
    Run complete financial analysis pipeline.

    This is the main entry point for the processing layer.

    Args:
        ticker: Stock ticker symbol
        income_statements: List of income statement API responses
        balance_sheets: List of balance sheet API responses
        cash_flows: List of cash flow API responses
        metrics: Financial metrics API response
        price_data: Price/quote API response
        holdings_by_investor: Dict mapping investor name to holdings
        insider_trades: List of insider trade API responses
        analyst_estimates: List of analyst estimate API responses
        company_facts: Company facts API response
        wacc: Weighted average cost of capital for EVA calculation

    Returns:
        AnalysisResult with complete analysis
    """
    result = AnalysisResult(
        ticker=ticker,
        company_name=company_facts.get('name', ticker) if company_facts else ticker,
        analysis_date=datetime.now().isoformat(),
    )

    # Track data quality issues
    if not income_statements:
        result.data_quality_notes.append("No income statements provided")
    if not balance_sheets:
        result.data_quality_notes.append("No balance sheets provided")
    if not cash_flows:
        result.data_quality_notes.append("No cash flows provided")

    # Extract company data
    company = extract_company_data(
        ticker=ticker,
        income_statements=income_statements or [],
        balance_sheets=balance_sheets or [],
        cash_flows=cash_flows or [],
        metrics=metrics or {},
        price_data=price_data or {},
        holdings_by_investor=holdings_by_investor,
        insider_trades=insider_trades,
        analyst_estimates=analyst_estimates,
        company_facts=company_facts,
    )
    result.company_data = company

    # Calculate all metrics
    analysis = calculate_all_metrics(company, wacc=wacc)
    result.comprehensive_analysis = analysis

    # Build summary
    result.summary = {
        "ticker": ticker,
        "company_name": result.company_name,
        "current_price": company.price.current_price,
        "market_cap": company.price.market_cap,
        "data_periods_annual": len(company.financials_annual),
        "data_periods_quarterly": len(company.financials_quarterly),
        "composite_scores": {
            "piotroski_f_score": analysis.piotroski.value if analysis.piotroski else None,
            "altman_z_score": analysis.altman_z.value if analysis.altman_z else None,
            "beneish_m_score": analysis.beneish_m.value if analysis.beneish_m else None,
            "ohlson_o_probability": analysis.ohlson_o.value if analysis.ohlson_o else None,
        },
        "quality_score": analysis.overall_quality_score,
        "red_flag_count": len(analysis.red_flags),
        "green_flag_count": len(analysis.green_flags),
    }

    return result


def format_for_expert(result: AnalysisResult, expert_type: str) -> str:
    """
    Format analysis for a specific expert type.

    Args:
        result: Complete analysis result
        expert_type: One of "buffett", "graham", "lynch", "wood", "soros", "dalio", "burry"

    Returns:
        Formatted string context for the expert
    """
    base_context = result.to_llm_context()

    # Add expert-specific emphasis
    expert_emphasis = {
        "buffett": [
            "\n## Buffett-Relevant Highlights",
            f"- Owner Earnings: See above",
            f"- FCF Conversion: {result.comprehensive_analysis.fcf_conversion.value if result.comprehensive_analysis and result.comprehensive_analysis.fcf_conversion else 'N/A'}%",
            f"- ROE Quality: See DuPont analysis above",
        ],
        "graham": [
            "\n## Graham-Relevant Highlights",
            f"- Altman Z-Score (Safety): {result.comprehensive_analysis.altman_z.value if result.comprehensive_analysis and result.comprehensive_analysis.altman_z else 'N/A'}",
            f"- Earnings Quality: See Beneish M-Score and Sloan Accrual above",
        ],
        "lynch": [
            "\n## Lynch-Relevant Highlights",
            f"- Growth Trends: See revenue/earnings trend analysis above",
            f"- Sustainable Growth Rate: {result.comprehensive_analysis.sustainable_growth.value if result.comprehensive_analysis and result.comprehensive_analysis.sustainable_growth else 'N/A'}%",
        ],
        "wood": [
            "\n## Wood-Relevant Highlights",
            f"- Gross Profitability: {result.comprehensive_analysis.gross_profitability.value if result.comprehensive_analysis and result.comprehensive_analysis.gross_profitability else 'N/A'}%",
            f"- Growth Trajectory: See trend analysis above",
        ],
        "soros": [
            "\n## Soros-Relevant Highlights",
            f"- Market Cap: ${result.company_data.price.market_cap:,.0f}" if result.company_data else "",
            "- (Price action and sentiment data from other sources)",
        ],
        "dalio": [
            "\n## Dalio-Relevant Highlights",
            f"- Altman Z-Score (Stress): {result.comprehensive_analysis.altman_z.value if result.comprehensive_analysis and result.comprehensive_analysis.altman_z else 'N/A'}",
            f"- Ohlson O-Score (Bankruptcy Risk): {result.comprehensive_analysis.ohlson_o.value if result.comprehensive_analysis and result.comprehensive_analysis.ohlson_o else 'N/A'}",
        ],
        "burry": [
            "\n## Burry-Relevant Highlights",
            f"- Beneish M-Score (Manipulation): {result.comprehensive_analysis.beneish_m.value if result.comprehensive_analysis and result.comprehensive_analysis.beneish_m else 'N/A'}",
            f"- Sloan Accrual Ratio: {result.comprehensive_analysis.sloan_accrual.value if result.comprehensive_analysis and result.comprehensive_analysis.sloan_accrual else 'N/A'}%",
            f"- All Red Flags: {len(result.comprehensive_analysis.red_flags) if result.comprehensive_analysis else 0}",
        ],
        "cro": [
             "\n## Chief Risk Officer Highlights",
             f"- Stressed ICR (Simulated): {result.comprehensive_analysis.stress_test_result.stressed_icr if result.comprehensive_analysis and result.comprehensive_analysis.stress_test_result else 'N/A'}",
             f"- Refinancing Risk: {result.comprehensive_analysis.refinancing_risk.interpretation if result.comprehensive_analysis and result.comprehensive_analysis.refinancing_risk else 'N/A'}",
             f"- Leverage Status: {result.comprehensive_analysis.leverage_ratio.interpretation if result.comprehensive_analysis and result.comprehensive_analysis.leverage_ratio else 'N/A'}",
        ]
    }

    emphasis = expert_emphasis.get(expert_type.lower(), [])
    return base_context + "\n".join(emphasis)
