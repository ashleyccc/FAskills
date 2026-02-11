"""
Credit Risk Metrics Calculator

This module calculates institutional credit risk metrics:
- Interest Coverage Ratio (ICR)
- Leverage Ratios (Net Debt/EBITDA, Debt/Capital)
- Refinancing Risk Indicator (Maturity Wall)
- Recession Stress Test (Simulating -15% Revenue, +200bps Rates)

Based on Basel III / CCAR principles.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class CreditMetricResult:
    value: float
    interpretation: str
    components: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)

@dataclass
class StressTestResult:
    scenario_name: str
    stressed_icr: float
    icr_change: float
    survives: bool
    details: Dict[str, float]

def calculate_icr(ebit: float, interest_expense: float) -> CreditMetricResult:
    """
    Interest Coverage Ratio = EBIT / Interest Expense
    """
    # Handle zero interest expense
    if interest_expense == 0:
        return CreditMetricResult(
            value=999.0, # Infinite coverage
            interpretation="No Interest Expense - Safe",
            components={"ebit": ebit, "interest": 0}
        )
    
    icr = ebit / interest_expense
    
    flags = []
    if icr < 1.0:
        interpretation = "DISTRESS - Cannot cover interest with earnings"
        flags.append("CRITICAL: ICR < 1.0 (Technical Default Risk)")
    elif icr < 1.5:
        interpretation = "Weak - Highly vulnerable"
        flags.append("High Risk: ICR < 1.5")
    elif icr < 3.0:
        interpretation = "Adequate - Investment Grade minimum"
    else:
        interpretation = "Strong coverage"
        
    return CreditMetricResult(
        value=round(icr, 2),
        interpretation=interpretation,
        components={"ebit": ebit, "interest": interest_expense},
        flags=flags
    )

def calculate_leverage(net_debt: float, ebitda: float) -> CreditMetricResult:
    """
    Leverage Ratio = Net Debt / EBITDA
    """
    if ebitda <= 0:
         return CreditMetricResult(
            value=999.0, 
            interpretation="Negative EBITDA - Assessment Meaningless (High Risk)",
            components={"net_debt": net_debt, "ebitda": ebitda},
            flags=["Negative EBITDA"]
        )
        
    leverage = net_debt / ebitda
    
    flags = []
    if leverage > 5.0:
        interpretation = "Highly Leveraged - Speculative Grade"
        flags.append("High Leverage > 5.0x")
    elif leverage > 4.0:
        interpretation = "Elevated Leverage"
    elif leverage > 2.0:
        interpretation = "Moderate Leverage"
    else:
        interpretation = "Low Leverage - Conservative"
        
    return CreditMetricResult(
        value=round(leverage, 2),
        interpretation=interpretation,
        components={"net_debt": net_debt, "ebitda": ebitda},
        flags=flags
    )

def calculate_refinancing_risk(
    short_term_debt: float,
    cash_and_equivalents: float,
    operating_cash_flow: float
) -> CreditMetricResult:
    """
    Maturity Wall Indicator = Short Term Debt / (Cash + OCF)
    Can the company pay off debt maturing in 12 months with current resources?
    """
    liquidity_sources = cash_and_equivalents + max(0, operating_cash_flow) # conservative OCF
    
    if liquidity_sources == 0:
         return CreditMetricResult(
            value=999.0, # Infinite risk if no liquidity
            interpretation="CRITICAL - No Liquidity for Maturities",
            components={"short_term_debt": short_term_debt, "liquidity": 0}
        )

    coverage = liquidity_sources / short_term_debt if short_term_debt > 0 else 999.0
    
    # Invert for "Risk Ratio": Debt / Liquidity
    risk_ratio = short_term_debt / liquidity_sources if liquidity_sources > 0 else 999.0
    
    flags = []
    if risk_ratio > 1.0:
        interpretation = "High Refinancing Risk - Needs external capital"
        flags.append("MATURITY WALL: Imminent debt exceeds liquidity")
    elif risk_ratio > 0.8:
        interpretation = "Tight Liquidity Position"
    else:
        interpretation = "Manageable Maturities"
        
    return CreditMetricResult(
        value=round(risk_ratio, 2),
        interpretation=interpretation,
        components={
            "short_term_debt": short_term_debt,
            "cash": cash_and_equivalents,
            "ocf": operating_cash_flow
        },
        flags=flags
    )

def run_recession_stress_test(
    ebit: float,
    interest_expense: float,
    revenue: float
) -> StressTestResult:
    """
    Simulate a 'Severe Adverse' Scenario:
    - Revenue drops 15% (assume high operating leverage, so EBIT drops 30%)
    - Interest rates rise -> Interest Expense increases 25%
    """
    
    stressed_revenue = revenue * 0.85
    # Simplified Operating Leverage assumption: 2x revenue drop impact on EBIT
    # Failure to cover fixed costs makes EBIT drop faster than revenue
    ebit_drop_pct = 0.30 
    stressed_ebit = ebit * (1 - ebit_drop_pct)
    
    stressed_interest = interest_expense * 1.25 # Refinancing at higher rates
    
    stressed_icr = stressed_ebit / stressed_interest if stressed_interest > 0 else 999.0
    
    survives = stressed_icr >= 1.0
    
    base_icr = ebit / interest_expense if interest_expense > 0 else 999.0
    
    return StressTestResult(
        scenario_name="2026 Recession (Rev -15%, Rates +200bps)",
        stressed_icr=round(stressed_icr, 2),
        icr_change=round(stressed_icr - base_icr, 2),
        survives=survives,
        details={
            "stressed_ebit": stressed_ebit,
            "stressed_interest": stressed_interest
        }
    )
