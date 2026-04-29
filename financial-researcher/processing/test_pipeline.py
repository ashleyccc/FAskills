"""
Test script for the financial processing pipeline.

Run: python -m processing.test_pipeline
"""

from processing import (
    run_analysis,
    format_for_expert,
    FinancialData,
    piotroski_f_score,
    altman_z_score,
    beneish_m_score,
    ohlson_o_score,
    sloan_accrual_ratio,
    owner_earnings,
    dupont_5_factor,
)


def test_individual_metrics():
    """Test individual metric calculations."""
    print("=" * 60)
    print("Testing Individual Metrics")
    print("=" * 60)

    # Test Piotroski F-Score
    print("\n1. Piotroski F-Score")
    piotroski = piotroski_f_score(
        net_income=10_000_000,
        operating_cash_flow=12_000_000,
        total_assets=50_000_000,
        long_term_debt=5_000_000,
        current_assets=20_000_000,
        current_liabilities=10_000_000,
        shares_outstanding=1_000_000,
        gross_profit=30_000_000,
        revenue=100_000_000,
        net_income_prev=8_000_000,
        total_assets_prev=45_000_000,
        long_term_debt_prev=6_000_000,
        current_assets_prev=18_000_000,
        current_liabilities_prev=9_000_000,
        shares_outstanding_prev=1_000_000,
        gross_profit_prev=25_000_000,
        revenue_prev=80_000_000,
    )
    print(f"   Score: {piotroski.value}/9")
    print(f"   Interpretation: {piotroski.interpretation}")
    print(f"   Components: {piotroski.components}")

    # Test Altman Z-Score
    print("\n2. Altman Z-Score")
    altman = altman_z_score(
        working_capital=10_000_000,
        retained_earnings=20_000_000,
        ebit=15_000_000,
        market_cap=200_000_000,
        revenue=100_000_000,
        total_assets=50_000_000,
        total_liabilities=30_000_000,
        is_manufacturing=True,
    )
    print(f"   Score: {altman.value}")
    print(f"   Interpretation: {altman.interpretation}")

    # Test Beneish M-Score
    print("\n3. Beneish M-Score")
    beneish = beneish_m_score(
        receivables=8_000_000,
        revenue=100_000_000,
        gross_profit=30_000_000,
        total_assets=50_000_000,
        ppe=15_000_000,
        depreciation=2_000_000,
        sga=10_000_000,
        total_debt=10_000_000,
        current_assets=20_000_000,
        current_liabilities=10_000_000,
        receivables_prev=7_000_000,
        revenue_prev=80_000_000,
        gross_profit_prev=25_000_000,
        total_assets_prev=45_000_000,
        ppe_prev=13_000_000,
        depreciation_prev=1_800_000,
        sga_prev=8_000_000,
        total_debt_prev=12_000_000,
        net_income=10_000_000,
        operating_cash_flow=12_000_000,
    )
    print(f"   Score: {beneish.value}")
    print(f"   Interpretation: {beneish.interpretation}")
    if beneish.flags:
        print(f"   Flags: {beneish.flags}")

    # Test Ohlson O-Score
    print("\n4. Ohlson O-Score")
    ohlson = ohlson_o_score(
        total_assets=50_000_000,
        total_liabilities=30_000_000,
        working_capital=10_000_000,
        current_liabilities=10_000_000,
        net_income=10_000_000,
        funds_from_operations=12_000_000,
        net_income_prev=8_000_000,
        total_liabilities_prev=28_000_000,
    )
    print(f"   Probability: {ohlson.value:.2%}")
    print(f"   Interpretation: {ohlson.interpretation}")

    # Test Sloan Accrual Ratio
    print("\n5. Sloan Accrual Ratio")
    sloan = sloan_accrual_ratio(
        net_income=10_000_000,
        operating_cash_flow=12_000_000,
        total_assets=50_000_000,
        total_assets_prev=45_000_000,
    )
    print(f"   Ratio: {sloan.value}%")
    print(f"   Interpretation: {sloan.interpretation}")

    # Test Owner Earnings
    print("\n6. Owner Earnings (Buffett)")
    oe = owner_earnings(
        net_income=10_000_000,
        depreciation=2_000_000,
        amortization=500_000,
        capex=3_000_000,
        working_capital_change=1_000_000,
        shares_outstanding=1_000_000,
    )
    print(f"   Owner Earnings: ${oe.value:,.0f}")
    print(f"   Per Share: ${oe.components['per_share']:.2f}")
    print(f"   Interpretation: {oe.interpretation}")

    # Test DuPont 5-Factor
    print("\n7. DuPont 5-Factor Analysis")
    dupont = dupont_5_factor(
        net_income=10_000_000,
        ebt=12_000_000,
        ebit=15_000_000,
        revenue=100_000_000,
        total_assets=50_000_000,
        shareholders_equity=20_000_000,
    )
    print(f"   ROE: {dupont.value}%")
    print(f"   Analysis: {dupont.interpretation}")
    print(f"   Components: {dupont.components}")

    print("\n" + "=" * 60)
    print("All individual metric tests passed!")
    print("=" * 60)


def test_full_pipeline():
    """Test the full analysis pipeline with mock data."""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline")
    print("=" * 60)

    # Mock API responses
    income_statements = [
        {
            "fiscal_year": 2024,
            "period": "annual",
            "revenue": 100_000_000,
            "cost_of_revenue": 70_000_000,
            "gross_profit": 30_000_000,
            "operating_income": 15_000_000,
            "ebit": 15_000_000,
            "ebitda": 17_000_000,
            "income_before_tax": 12_000_000,
            "income_tax_expense": 2_000_000,
            "net_income": 10_000_000,
            "eps": 10.0,
            "weighted_average_shares_outstanding": 1_000_000,
            "depreciation_and_amortization": 2_000_000,
            "selling_general_and_administrative_expenses": 10_000_000,
        },
        {
            "fiscal_year": 2023,
            "period": "annual",
            "revenue": 80_000_000,
            "cost_of_revenue": 55_000_000,
            "gross_profit": 25_000_000,
            "operating_income": 12_000_000,
            "ebit": 12_000_000,
            "ebitda": 14_000_000,
            "income_before_tax": 10_000_000,
            "income_tax_expense": 2_000_000,
            "net_income": 8_000_000,
            "eps": 8.0,
            "weighted_average_shares_outstanding": 1_000_000,
            "depreciation_and_amortization": 1_800_000,
            "selling_general_and_administrative_expenses": 8_000_000,
        },
    ]

    balance_sheets = [
        {
            "fiscal_year": 2024,
            "period": "annual",
            "cash_and_cash_equivalents": 15_000_000,
            "accounts_receivable": 8_000_000,
            "inventory": 5_000_000,
            "total_current_assets": 30_000_000,
            "property_plant_and_equipment_net": 15_000_000,
            "total_assets": 60_000_000,
            "accounts_payable": 5_000_000,
            "total_current_liabilities": 12_000_000,
            "long_term_debt": 8_000_000,
            "total_debt": 10_000_000,
            "total_liabilities": 30_000_000,
            "total_stockholders_equity": 30_000_000,
            "retained_earnings": 25_000_000,
        },
        {
            "fiscal_year": 2023,
            "period": "annual",
            "cash_and_cash_equivalents": 12_000_000,
            "accounts_receivable": 7_000_000,
            "inventory": 4_000_000,
            "total_current_assets": 25_000_000,
            "property_plant_and_equipment_net": 13_000_000,
            "total_assets": 50_000_000,
            "accounts_payable": 4_000_000,
            "total_current_liabilities": 10_000_000,
            "long_term_debt": 10_000_000,
            "total_debt": 12_000_000,
            "total_liabilities": 28_000_000,
            "total_stockholders_equity": 22_000_000,
            "retained_earnings": 18_000_000,
        },
    ]

    cash_flows = [
        {
            "fiscal_year": 2024,
            "period": "annual",
            "operating_cash_flow": 14_000_000,
            "capital_expenditure": -3_000_000,
            "free_cash_flow": 11_000_000,
            "dividends_paid": -2_000_000,
            "common_stock_repurchased": -1_000_000,
        },
        {
            "fiscal_year": 2023,
            "period": "annual",
            "operating_cash_flow": 11_000_000,
            "capital_expenditure": -2_500_000,
            "free_cash_flow": 8_500_000,
            "dividends_paid": -1_500_000,
        },
    ]

    metrics = {
        "pe_ratio": 20.0,
        "pb_ratio": 6.67,
        "roe": 0.333,
        "roa": 0.167,
        "roic": 0.25,
        "current_ratio": 2.5,
        "debt_to_equity": 0.33,
    }

    price_data = {
        "price": 200.0,
        "market_cap": 200_000_000,
        "shares_outstanding": 1_000_000,
    }

    company_facts = {
        "name": "Test Company Inc.",
        "sector": "Technology",
        "industry": "Software",
    }

    # Run full analysis
    print("\nRunning full analysis pipeline...")
    result = run_analysis(
        ticker="TEST",
        income_statements=income_statements,
        balance_sheets=balance_sheets,
        cash_flows=cash_flows,
        metrics=metrics,
        price_data=price_data,
        company_facts=company_facts,
    )

    print(f"\nCompany: {result.company_name}")
    print(f"Ticker: {result.ticker}")
    print(f"Analysis Date: {result.analysis_date}")

    print("\n--- Summary ---")
    print(f"Current Price: ${result.summary.get('current_price', 0):,.2f}")
    print(f"Market Cap: ${result.summary.get('market_cap', 0):,.0f}")
    print(f"Annual Periods: {result.summary.get('data_periods_annual', 0)}")

    scores = result.summary.get('composite_scores', {})
    print(f"\nPiotroski F-Score: {scores.get('piotroski_f_score')}/9")
    print(f"Altman Z-Score: {scores.get('altman_z_score')}")
    print(f"Beneish M-Score: {scores.get('beneish_m_score')}")
    print(f"Ohlson O-Score: {scores.get('ohlson_o_probability')}")

    print(f"\nOverall Quality Score: {result.summary.get('quality_score')}/100")
    print(f"Red Flags: {result.summary.get('red_flag_count')}")
    print(f"Green Flags: {result.summary.get('green_flag_count')}")

    # Test LLM context generation
    print("\n--- LLM Context Preview ---")
    context = result.to_llm_context()
    # Print first 1000 chars
    print(context[:1000] + "..." if len(context) > 1000 else context)

    # Test expert-specific formatting
    print("\n--- Buffett Expert Context Preview ---")
    buffett_context = format_for_expert(result, "buffett")
    print(buffett_context[-500:])  # Last 500 chars

    print("\n" + "=" * 60)
    print("Full pipeline test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_individual_metrics()
    test_full_pipeline()
