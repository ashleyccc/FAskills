"""
Data Extractor for Financial Datasets API

Maps raw API responses to calculator inputs.
Handles missing data gracefully.

API Endpoints Used:
- /financials/ (income statements, balance sheets, cash flows)
- /financial-metrics/ (pre-calculated ratios)
- /prices/ (stock prices)
- /institutional-ownership/ (13-F holdings)
- /insider-trades/ (insider transactions)
- /analyst-estimates/ (EPS estimates)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json


@dataclass
class FinancialData:
    """Extracted financial data for a single period."""
    period: str  # "annual" or "quarterly"
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    report_date: Optional[str] = None

    # Income Statement
    revenue: float = 0
    cost_of_revenue: float = 0
    gross_profit: float = 0
    operating_expenses: float = 0
    sga_expense: float = 0
    rd_expense: float = 0
    depreciation: float = 0
    amortization: float = 0  # Separate from depreciation when available
    depreciation_and_amortization: float = 0  # Combined D&A
    operating_income: float = 0
    ebit: float = 0
    ebitda: float = 0
    interest_expense: float = 0
    ebt: float = 0  # Earnings before tax
    income_tax: float = 0
    net_income: float = 0
    eps: float = 0
    shares_outstanding: float = 0
    shares_outstanding_diluted: float = 0

    # Balance Sheet
    cash: float = 0
    short_term_investments: float = 0
    accounts_receivable: float = 0
    inventory: float = 0
    current_assets: float = 0
    ppe_gross: float = 0
    ppe_net: float = 0
    goodwill: float = 0
    intangible_assets: float = 0
    total_assets: float = 0
    accounts_payable: float = 0
    short_term_debt: float = 0
    current_liabilities: float = 0
    long_term_debt: float = 0
    total_debt: float = 0
    total_liabilities: float = 0
    shareholders_equity: float = 0
    retained_earnings: float = 0
    book_value_per_share: float = 0

    # Cash Flow Statement
    operating_cash_flow: float = 0
    capex: float = 0
    free_cash_flow: float = 0
    dividends_paid: float = 0
    shares_repurchased: float = 0
    shares_issued: float = 0
    debt_repaid: float = 0
    debt_issued: float = 0

    # Derived
    working_capital: float = 0
    enterprise_value: float = 0
    market_cap: float = 0


@dataclass
class MetricsData:
    """Pre-calculated metrics from API (don't recalculate these)."""
    # Valuation
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    peg_ratio: Optional[float] = None
    fcf_yield: Optional[float] = None

    # Profitability
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None

    # Efficiency
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    dso: Optional[float] = None  # Days sales outstanding

    # Liquidity
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None

    # Leverage
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Growth
    revenue_growth: Optional[float] = None
    eps_growth: Optional[float] = None
    fcf_growth: Optional[float] = None

    # Per Share
    eps: Optional[float] = None
    book_value_per_share: Optional[float] = None
    fcf_per_share: Optional[float] = None
    dividend_per_share: Optional[float] = None


@dataclass
class PriceData:
    """Price and market data."""
    current_price: float = 0
    market_cap: float = 0
    enterprise_value: float = 0
    shares_outstanding: float = 0
    avg_volume: float = 0
    week_52_high: float = 0
    week_52_low: float = 0
    price_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HoldingsData:
    """Institutional ownership data."""
    investor_name: str = ""
    shares_held: float = 0
    market_value: float = 0
    portfolio_weight: float = 0
    change_in_shares: float = 0
    change_percent: float = 0
    report_date: str = ""
    quarters_held: int = 0


@dataclass
class InsiderData:
    """Insider transaction data."""
    insider_name: str = ""
    title: str = ""
    transaction_type: str = ""  # "buy" or "sell"
    shares: float = 0
    price: float = 0
    value: float = 0
    date: str = ""


@dataclass
class CompanyData:
    """Complete extracted data for a company."""
    ticker: str
    company_name: str = ""
    sector: str = ""
    industry: str = ""

    # Time series (most recent first)
    financials_annual: List[FinancialData] = field(default_factory=list)
    financials_quarterly: List[FinancialData] = field(default_factory=list)

    # Current metrics
    metrics: MetricsData = field(default_factory=MetricsData)
    price: PriceData = field(default_factory=PriceData)

    # Holdings and insider data
    holdings: Dict[str, List[HoldingsData]] = field(default_factory=dict)  # keyed by investor
    insider_trades: List[InsiderData] = field(default_factory=list)

    # Analyst estimates
    eps_estimates: Dict[str, float] = field(default_factory=dict)  # keyed by period

    # Data quality
    data_completeness: float = 1.0


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_income_statement(raw: Dict[str, Any]) -> Dict[str, float]:
    """Extract income statement fields from API response."""
    return {
        'revenue': raw.get('revenue', 0) or 0,
        'cost_of_revenue': raw.get('cost_of_revenue', 0) or 0,
        'gross_profit': raw.get('gross_profit', 0) or 0,
        'operating_expenses': raw.get('operating_expenses', 0) or 0,
        'sga_expense': raw.get('selling_general_and_administrative_expenses', 0) or 0,
        'rd_expense': raw.get('research_and_development_expenses', 0) or 0,
        'depreciation': raw.get('depreciation', 0) or raw.get('depreciation_expense', 0) or 0,
        'amortization': raw.get('amortization', 0) or raw.get('amortization_expense', 0) or 0,
        'depreciation_and_amortization': raw.get('depreciation_and_amortization', 0) or 0,
        'operating_income': raw.get('operating_income', 0) or 0,
        'ebit': raw.get('ebit', 0) or raw.get('operating_income', 0) or 0,
        'ebitda': raw.get('ebitda', 0) or 0,
        'interest_expense': raw.get('interest_expense', 0) or 0,
        'ebt': raw.get('income_before_tax', 0) or 0,
        'income_tax': raw.get('income_tax_expense', 0) or 0,
        'net_income': raw.get('net_income', 0) or 0,
        'eps': raw.get('eps', 0) or raw.get('earnings_per_share', 0) or 0,
        'shares_outstanding': raw.get('weighted_average_shares_outstanding', 0) or 0,
        'shares_outstanding_diluted': raw.get('weighted_average_shares_outstanding_diluted', 0) or 0,
    }


def extract_balance_sheet(raw: Dict[str, Any]) -> Dict[str, float]:
    """Extract balance sheet fields from API response."""
    return {
        'cash': raw.get('cash_and_cash_equivalents', 0) or 0,
        'short_term_investments': raw.get('short_term_investments', 0) or 0,
        'accounts_receivable': raw.get('accounts_receivable', 0) or raw.get('net_receivables', 0) or 0,
        'inventory': raw.get('inventory', 0) or 0,
        'current_assets': raw.get('total_current_assets', 0) or 0,
        'ppe_gross': raw.get('property_plant_and_equipment', 0) or 0,
        'ppe_net': raw.get('property_plant_and_equipment_net', 0) or raw.get('net_ppe', 0) or 0,
        'goodwill': raw.get('goodwill', 0) or 0,
        'intangible_assets': raw.get('intangible_assets', 0) or 0,
        'total_assets': raw.get('total_assets', 0) or 0,
        'accounts_payable': raw.get('accounts_payable', 0) or 0,
        'short_term_debt': raw.get('short_term_debt', 0) or 0,
        'current_liabilities': raw.get('total_current_liabilities', 0) or 0,
        'long_term_debt': raw.get('long_term_debt', 0) or 0,
        'total_debt': raw.get('total_debt', 0) or 0,
        'total_liabilities': raw.get('total_liabilities', 0) or 0,
        'shareholders_equity': raw.get('total_stockholders_equity', 0) or raw.get('total_equity', 0) or 0,
        'retained_earnings': raw.get('retained_earnings', 0) or 0,
    }


def extract_cash_flow(raw: Dict[str, Any]) -> Dict[str, float]:
    """Extract cash flow statement fields from API response."""
    return {
        'operating_cash_flow': raw.get('operating_cash_flow', 0) or raw.get('net_cash_provided_by_operating_activities', 0) or 0,
        'capex': abs(raw.get('capital_expenditure', 0) or raw.get('capital_expenditures', 0) or 0),
        'free_cash_flow': raw.get('free_cash_flow', 0) or 0,
        'dividends_paid': raw.get('dividends_paid', 0) or raw.get('payment_of_dividends', 0) or 0,
        'shares_repurchased': raw.get('common_stock_repurchased', 0) or 0,
        'shares_issued': raw.get('common_stock_issued', 0) or 0,
        'debt_repaid': raw.get('debt_repayment', 0) or 0,
        'debt_issued': raw.get('debt_issuance', 0) or 0,
    }


def extract_financial_period(
    income_stmt: Dict[str, Any],
    balance_sheet: Dict[str, Any],
    cash_flow: Dict[str, Any],
    period: str = "annual"
) -> FinancialData:
    """Combine all statements into a single FinancialData object."""

    # Extract from each statement
    inc = extract_income_statement(income_stmt)
    bal = extract_balance_sheet(balance_sheet)
    cf = extract_cash_flow(cash_flow)

    # Calculate derived metrics
    working_capital = bal['current_assets'] - bal['current_liabilities']

    # Calculate free cash flow if not provided
    fcf = cf['free_cash_flow']
    if fcf == 0 and cf['operating_cash_flow'] != 0:
        fcf = cf['operating_cash_flow'] - cf['capex']

    return FinancialData(
        period=period,
        fiscal_year=income_stmt.get('fiscal_year', 0),
        fiscal_quarter=income_stmt.get('fiscal_quarter'),
        report_date=income_stmt.get('report_period') or income_stmt.get('date'),

        # Income statement
        revenue=inc['revenue'],
        cost_of_revenue=inc['cost_of_revenue'],
        gross_profit=inc['gross_profit'],
        operating_expenses=inc['operating_expenses'],
        sga_expense=inc['sga_expense'],
        rd_expense=inc['rd_expense'],
        depreciation=inc['depreciation'] or inc['depreciation_and_amortization'],
        amortization=inc['amortization'],
        depreciation_and_amortization=inc['depreciation_and_amortization'] or (inc['depreciation'] + inc['amortization']),
        operating_income=inc['operating_income'],
        ebit=inc['ebit'],
        ebitda=inc['ebitda'],
        interest_expense=inc['interest_expense'],
        ebt=inc['ebt'],
        income_tax=inc['income_tax'],
        net_income=inc['net_income'],
        eps=inc['eps'],
        shares_outstanding=inc['shares_outstanding'],
        shares_outstanding_diluted=inc['shares_outstanding_diluted'],

        # Balance sheet
        cash=bal['cash'],
        short_term_investments=bal['short_term_investments'],
        accounts_receivable=bal['accounts_receivable'],
        inventory=bal['inventory'],
        current_assets=bal['current_assets'],
        ppe_gross=bal['ppe_gross'],
        ppe_net=bal['ppe_net'],
        goodwill=bal['goodwill'],
        intangible_assets=bal['intangible_assets'],
        total_assets=bal['total_assets'],
        accounts_payable=bal['accounts_payable'],
        short_term_debt=bal['short_term_debt'],
        current_liabilities=bal['current_liabilities'],
        long_term_debt=bal['long_term_debt'],
        total_debt=bal['total_debt'],
        total_liabilities=bal['total_liabilities'],
        shareholders_equity=bal['shareholders_equity'],
        retained_earnings=bal['retained_earnings'],

        # Cash flow
        operating_cash_flow=cf['operating_cash_flow'],
        capex=cf['capex'],
        free_cash_flow=fcf,
        dividends_paid=cf['dividends_paid'],
        shares_repurchased=cf['shares_repurchased'],
        shares_issued=cf['shares_issued'],
        debt_repaid=cf['debt_repaid'],
        debt_issued=cf['debt_issued'],

        # Derived
        working_capital=working_capital,
    )


def extract_metrics(raw: Dict[str, Any]) -> MetricsData:
    """Extract pre-calculated metrics from API response."""
    return MetricsData(
        # Valuation
        pe_ratio=raw.get('price_to_earnings_ratio') or raw.get('pe_ratio'),
        pb_ratio=raw.get('price_to_book_ratio') or raw.get('pb_ratio'),
        ps_ratio=raw.get('price_to_sales_ratio') or raw.get('ps_ratio'),
        ev_to_ebitda=raw.get('enterprise_value_to_ebitda') or raw.get('ev_to_ebitda'),
        ev_to_revenue=raw.get('enterprise_value_to_revenue') or raw.get('ev_to_revenue'),
        peg_ratio=raw.get('peg_ratio'),
        fcf_yield=raw.get('free_cash_flow_yield') or raw.get('fcf_yield'),

        # Profitability
        gross_margin=raw.get('gross_profit_margin') or raw.get('gross_margin'),
        operating_margin=raw.get('operating_profit_margin') or raw.get('operating_margin'),
        net_margin=raw.get('net_profit_margin') or raw.get('net_margin'),
        roe=raw.get('return_on_equity') or raw.get('roe'),
        roa=raw.get('return_on_assets') or raw.get('roa'),
        roic=raw.get('return_on_invested_capital') or raw.get('roic'),

        # Efficiency
        asset_turnover=raw.get('asset_turnover'),
        inventory_turnover=raw.get('inventory_turnover'),
        receivables_turnover=raw.get('receivables_turnover'),
        dso=raw.get('days_sales_outstanding') or raw.get('dso'),

        # Liquidity
        current_ratio=raw.get('current_ratio'),
        quick_ratio=raw.get('quick_ratio'),
        cash_ratio=raw.get('cash_ratio'),

        # Leverage
        debt_to_equity=raw.get('debt_to_equity') or raw.get('debt_to_equity_ratio'),
        debt_to_assets=raw.get('debt_to_assets') or raw.get('debt_to_assets_ratio'),
        interest_coverage=raw.get('interest_coverage') or raw.get('interest_coverage_ratio'),

        # Growth
        revenue_growth=raw.get('revenue_growth'),
        eps_growth=raw.get('eps_growth') or raw.get('earnings_per_share_growth'),
        fcf_growth=raw.get('free_cash_flow_growth'),

        # Per Share
        eps=raw.get('earnings_per_share') or raw.get('eps'),
        book_value_per_share=raw.get('book_value_per_share'),
        fcf_per_share=raw.get('free_cash_flow_per_share'),
        dividend_per_share=raw.get('dividend_per_share'),
    )


def extract_holdings(raw_list: List[Dict[str, Any]], investor_name: str) -> List[HoldingsData]:
    """Extract holdings data for a specific investor."""
    holdings = []
    for raw in raw_list:
        holdings.append(HoldingsData(
            investor_name=investor_name,
            shares_held=raw.get('shares', 0) or raw.get('shares_held', 0) or 0,
            market_value=raw.get('market_value', 0) or raw.get('value', 0) or 0,
            portfolio_weight=raw.get('portfolio_weight', 0) or raw.get('weight', 0) or 0,
            change_in_shares=raw.get('change_in_shares', 0) or raw.get('shares_change', 0) or 0,
            change_percent=raw.get('change_percent', 0) or 0,
            report_date=raw.get('report_period', '') or raw.get('date', ''),
        ))
    return holdings


def extract_insider_trades(raw_list: List[Dict[str, Any]]) -> List[InsiderData]:
    """Extract insider transaction data."""
    trades = []
    for raw in raw_list:
        tx_type = raw.get('transaction_type', '').lower()
        if 'buy' in tx_type or 'purchase' in tx_type or 'acquisition' in tx_type:
            tx_type = 'buy'
        elif 'sell' in tx_type or 'sale' in tx_type or 'disposition' in tx_type:
            tx_type = 'sell'

        trades.append(InsiderData(
            insider_name=raw.get('insider_name', '') or raw.get('name', ''),
            title=raw.get('insider_title', '') or raw.get('title', ''),
            transaction_type=tx_type,
            shares=abs(raw.get('shares', 0) or raw.get('transaction_shares', 0) or 0),
            price=raw.get('price', 0) or raw.get('price_per_share', 0) or 0,
            value=abs(raw.get('value', 0) or raw.get('transaction_value', 0) or 0),
            date=raw.get('transaction_date', '') or raw.get('date', ''),
        ))
    return trades


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_company_data(
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
) -> CompanyData:
    """
    Extract all data for a company from raw API responses.

    Args:
        ticker: Stock ticker symbol
        income_statements: List of income statement responses (most recent first)
        balance_sheets: List of balance sheet responses
        cash_flows: List of cash flow responses
        metrics: Financial metrics response
        price_data: Price/quote response
        holdings_by_investor: Dict mapping investor name to their holdings
        insider_trades: List of insider trade responses
        analyst_estimates: List of EPS estimate responses
        company_facts: Company overview/facts response

    Returns:
        CompanyData object with all extracted data
    """
    company = CompanyData(ticker=ticker)

    # Company info
    if company_facts:
        company.company_name = company_facts.get('name', '') or company_facts.get('company_name', '')
        company.sector = company_facts.get('sector', '')
        company.industry = company_facts.get('industry', '')

    # Match statements by period and combine
    # Assuming statements are sorted by date, most recent first
    annual_periods = {}
    quarterly_periods = {}

    for inc in income_statements:
        period_type = inc.get('period', 'annual')
        year = inc.get('fiscal_year', 0)
        quarter = inc.get('fiscal_quarter')
        key = f"{year}-Q{quarter}" if quarter else str(year)

        if period_type == 'quarterly' and quarter:
            if key not in quarterly_periods:
                quarterly_periods[key] = {'income': inc, 'balance': None, 'cashflow': None}
            else:
                quarterly_periods[key]['income'] = inc
        else:
            if key not in annual_periods:
                annual_periods[key] = {'income': inc, 'balance': None, 'cashflow': None}
            else:
                annual_periods[key]['income'] = inc

    for bal in balance_sheets:
        period_type = bal.get('period', 'annual')
        year = bal.get('fiscal_year', 0)
        quarter = bal.get('fiscal_quarter')
        key = f"{year}-Q{quarter}" if quarter else str(year)

        target = quarterly_periods if period_type == 'quarterly' and quarter else annual_periods
        if key in target:
            target[key]['balance'] = bal
        else:
            target[key] = {'income': {}, 'balance': bal, 'cashflow': None}

    for cf in cash_flows:
        period_type = cf.get('period', 'annual')
        year = cf.get('fiscal_year', 0)
        quarter = cf.get('fiscal_quarter')
        key = f"{year}-Q{quarter}" if quarter else str(year)

        target = quarterly_periods if period_type == 'quarterly' and quarter else annual_periods
        if key in target:
            target[key]['cashflow'] = cf
        else:
            target[key] = {'income': {}, 'balance': {}, 'cashflow': cf}

    # Extract annual financials
    for key in sorted(annual_periods.keys(), reverse=True):
        data = annual_periods[key]
        fin = extract_financial_period(
            data.get('income', {}),
            data.get('balance', {}),
            data.get('cashflow', {}),
            period='annual'
        )
        company.financials_annual.append(fin)

    # Extract quarterly financials
    for key in sorted(quarterly_periods.keys(), reverse=True):
        data = quarterly_periods[key]
        fin = extract_financial_period(
            data.get('income', {}),
            data.get('balance', {}),
            data.get('cashflow', {}),
            period='quarterly'
        )
        company.financials_quarterly.append(fin)

    # Extract metrics
    if metrics:
        company.metrics = extract_metrics(metrics)

    # Extract price data
    if price_data:
        company.price = PriceData(
            current_price=price_data.get('price', 0) or price_data.get('close', 0) or 0,
            market_cap=price_data.get('market_cap', 0) or price_data.get('marketCap', 0) or 0,
            shares_outstanding=price_data.get('shares_outstanding', 0) or 0,
        )

    # Extract holdings
    if holdings_by_investor:
        for investor, holdings_list in holdings_by_investor.items():
            company.holdings[investor] = extract_holdings(holdings_list, investor)

    # Extract insider trades
    if insider_trades:
        company.insider_trades = extract_insider_trades(insider_trades)

    # Extract analyst estimates
    if analyst_estimates:
        for est in analyst_estimates:
            period = est.get('fiscal_period', '')
            eps = est.get('earnings_per_share', 0)
            if period and eps:
                company.eps_estimates[period] = eps

    # Calculate data completeness
    total_fields = 0
    filled_fields = 0
    if company.financials_annual:
        latest = company.financials_annual[0]
        for field_name in ['revenue', 'net_income', 'total_assets', 'operating_cash_flow']:
            total_fields += 1
            if getattr(latest, field_name, 0) != 0:
                filled_fields += 1

    company.data_completeness = filled_fields / total_fields if total_fields > 0 else 0

    return company


def get_current_and_previous(financials: List[FinancialData]) -> Tuple[FinancialData, FinancialData]:
    """Get current and previous year financial data."""
    if len(financials) >= 2:
        return financials[0], financials[1]
    elif len(financials) == 1:
        # Return same data for both (will result in no change metrics)
        return financials[0], financials[0]
    else:
        # Return empty data
        empty = FinancialData(period='annual', fiscal_year=0)
        return empty, empty
