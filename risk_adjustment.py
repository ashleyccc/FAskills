import pandas as pd
import numpy as np

def calculate_volatility(historical_prices: pd.DataFrame) -> pd.Series:
    """
    Calculates annualized volatility from daily historical prices.
    """
    daily_returns = historical_prices.pct_change()
    volatility = daily_returns.std() * np.sqrt(252)
    return volatility

def min_max_scale(series: pd.Series) -> pd.Series:
    """
    Applies Min-Max scaling to a pandas Series, binding values between 0 and 1.
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(1.0, index=series.index)
    return (series - min_val) / (max_val - min_val)

def apply_risk_adjusted_layer(
    screened_df: pd.DataFrame, 
    historical_prices: pd.DataFrame, 
    alpha: float = 0.5, 
    top_n: int = 15,
    risk_metric_choice: str = "Both"
) -> pd.DataFrame:
    """
    Applies the Risk-Adjusted Preference Layer.
    Calculates Volatility, applies Min-Max scaling, blends with Valuation, and actively filters Top N.
    """
    if screened_df.empty:
        return screened_df
        
    df = screened_df.copy()
    df.set_index("Ticker", inplace=True)
    
    # Calculate Volatility
    volatility = calculate_volatility(historical_prices)
    
    # Merge risk metrics into the dataframe
    df["Raw Volatility"] = volatility
    
    # Handle missing values by assigning median or dropping
    df.dropna(subset=["Raw Volatility", "Raw Beta"], inplace=True)
    
    if df.empty:
        return df.reset_index()

    # 1. Min-Max Scale Valuation Quality (Margin of Safety)
    df["Min-Max Valuation Score"] = min_max_scale(df["Margin of Safety"])
    
    # 2. Min-Max Scale Risk Metrics and Invert to get Safety
    scaled_vol = min_max_scale(df["Raw Volatility"])
    inverted_vol = 1.0 - scaled_vol
    
    scaled_beta = min_max_scale(df["Raw Beta"])
    inverted_beta = 1.0 - scaled_beta
    
    # Multi-Metric Safety Score
    if risk_metric_choice == "Volatility Only":
        df["Min-Max Safety Score"] = inverted_vol
    elif risk_metric_choice == "Beta Only":
        df["Min-Max Safety Score"] = inverted_beta
    else:
        df["Min-Max Safety Score"] = 0.5 * inverted_vol + 0.5 * inverted_beta
    
    # 3. Alpha-Controlled Blend
    df["Final Blended Score"] = (alpha * df["Min-Max Valuation Score"]) + ((1.0 - alpha) * df["Min-Max Safety Score"])
    
    # 4. Re-Ranking & Active Filtering
    df.sort_values("Final Blended Score", ascending=False, inplace=True)
    df["Pipeline Rank"] = range(1, len(df) + 1)
    
    top_candidates = df.head(top_n).reset_index()
    
    return top_candidates
