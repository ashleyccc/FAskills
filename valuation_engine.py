import pandas as pd

def run_dcf(fcf, shares_outstanding, current_price, discount_rate=0.10, short_term_growth=0.05, terminal_growth_rate=0.02, years=5):
    """
    Standard DCF calculation to compute intrinsic value and margin of safety.
    """
    if fcf is None or shares_outstanding is None or fcf <= 0 or shares_outstanding <= 0:
        return None
        
    # Project future FCFs
    projected_fcfs = [fcf * (1 + short_term_growth)**i for i in range(1, years + 1)]
    
    # Discount projected FCFs
    discounted_fcfs = [cf / ((1 + discount_rate)**i) for i, cf in enumerate(projected_fcfs, 1)]
    
    # Terminal Value
    terminal_value = (projected_fcfs[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
    discounted_tv = terminal_value / ((1 + discount_rate)**years)
    
    enterprise_value = sum(discounted_fcfs) + discounted_tv
    
    # Assuming Equity Value roughly equals Enterprise Value for prototyping
    equity_value = enterprise_value 
    
    intrinsic_value_per_share = equity_value / shares_outstanding
    
    if current_price and current_price > 0:
        margin_of_safety = (intrinsic_value_per_share - current_price) / current_price
    else:
        margin_of_safety = None
        
    return {
        "intrinsic_value": intrinsic_value_per_share,
        "margin_of_safety": margin_of_safety,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value
    }

def generate_dcf_sensitivity(fcf, shares_outstanding, current_price, base_wacc, base_growth, terminal_growth):
    """
    Generates a 2D matrix of Intrinsic Value Per Share across different WACCs and Short-term Growth Rates.
    """
    wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
    growth_range = [base_growth - 0.02, base_growth - 0.01, base_growth, base_growth + 0.01, base_growth + 0.02]
    
    matrix = []
    for g in growth_range:
        row = {"Growth Rate": f"{g*100:.1f}%"}
        for w in wacc_range:
            res = run_dcf(fcf, shares_outstanding, current_price, discount_rate=w, short_term_growth=g, terminal_growth_rate=terminal_growth)
            val = res["intrinsic_value"] if res else 0.0
            row[f"WACC {w*100:.1f}%"] = f"${val:.2f}"
        matrix.append(row)
        
    return pd.DataFrame(matrix)

def screen_stocks(stock_data: dict, min_margin_of_safety: float, wacc: float = 0.10, short_term_growth: float = 0.05, terminal_growth: float = 0.02) -> pd.DataFrame:
    """
    Takes a dictionary of stock data (with fundamental info) and runs DCF to screen undervalued stocks.
    Uses globally defined WACC and Growth assumptions.
    """
    results = []
    for ticker, data in stock_data.items():
        if data is None:
            continue
            
        dcf_result = run_dcf(
            fcf=data.get("fcf"),
            shares_outstanding=data.get("shares_outstanding"),
            current_price=data.get("current_price"),
            discount_rate=wacc,
            short_term_growth=short_term_growth,
            terminal_growth_rate=terminal_growth
        )
        
        if dcf_result and dcf_result["margin_of_safety"] is not None:
            if dcf_result["margin_of_safety"] >= min_margin_of_safety:
                results.append({
                    "Ticker": ticker,
                    "Current Price": data.get("current_price"),
                    "Intrinsic Value": dcf_result["intrinsic_value"],
                    "Margin of Safety": dcf_result["margin_of_safety"],
                    "Raw Beta": data.get("beta")
                })
                
    return pd.DataFrame(results)
