import numpy as np
import pandas as pd
from scipy.optimize import minimize

def optimize_portfolio(tickers: list, historical_prices: pd.DataFrame, max_weight: float = 0.20, objective: str = "Max Sharpe") -> dict:
    """
    Mean-Variance Optimization with explicit constraints.
    Supports "Max Sharpe" and "Min Variance" objectives.
    """
    if not tickers or historical_prices.empty:
        return {"weights": {}, "expected_return": 0.0, "expected_volatility": 0.0, "sharpe_ratio": 0.0}
        
    prices = historical_prices[tickers]
    returns = prices.pct_change().dropna()
    
    if returns.empty:
        w = {t: 1.0/len(tickers) for t in tickers}
        return {"weights": w, "expected_return": 0.0, "expected_volatility": 0.0, "sharpe_ratio": 0.0}
        
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    num_assets = len(tickers)
    risk_free_rate = 0.02
    
    def portfolio_annualized_performance(weights):
        ret = np.sum(mean_returns * weights)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return ret, vol
        
    def negative_sharpe(weights):
        ret, vol = portfolio_annualized_performance(weights)
        if vol == 0: return 0
        return -(ret - risk_free_rate) / vol
        
    def portfolio_variance(weights):
        ret, vol = portfolio_annualized_performance(weights)
        return vol**2
        
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    bounds = tuple((0.0, max_weight) for _ in range(num_assets))
    init_guess = num_assets * [1.0 / num_assets]
    
    obj_function = portfolio_variance if objective == "Min Variance" else negative_sharpe
    
    try:
        opt_result = minimize(obj_function, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        optimal_weights = opt_result.x if opt_result.success else np.array(init_guess)
    except Exception:
        optimal_weights = np.array(init_guess)
        
    weight_dict = {ticker: round(weight, 4) for ticker, weight in zip(tickers, optimal_weights)}
    final_ret, final_vol = portfolio_annualized_performance(optimal_weights)
    sharpe = (final_ret - risk_free_rate) / final_vol if final_vol > 0 else 0.0
    
    return {
        "weights": weight_dict,
        "expected_return": final_ret,
        "expected_volatility": final_vol,
        "sharpe_ratio": sharpe
    }

def generate_efficient_frontier(tickers: list, historical_prices: pd.DataFrame, num_portfolios: int = 1500):
    if not tickers or historical_prices.empty:
        return pd.DataFrame()
        
    prices = historical_prices[tickers]
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    num_assets = len(tickers)
    risk_free_rate = 0.02
    
    results = np.zeros((3, num_portfolios))
    for i in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        
        ret = np.sum(mean_returns * weights)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0
        
        results[0,i] = vol
        results[1,i] = ret
        results[2,i] = sharpe
        
    return pd.DataFrame(results.T, columns=['Volatility', 'Return', 'Sharpe Ratio'])
