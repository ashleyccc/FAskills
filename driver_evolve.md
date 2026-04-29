# /driver:evolve

## Iterative Development Process

### Iteration 1: The Base Pipeline
We started by establishing the core math. `valuation_engine.py` was built to compute basic DCF models, and `portfolio_optimizer.py` was built to handle the SciPy constraints. We mapped them into a simple, single-page Streamlit app (`app.py`).

### Iteration 2: Live Data & SSL Patching
The pipeline initially relied on mock data. We evolved the `data_client.py` to connect directly to the Yahoo Finance API using `yfinance`. We encountered a severe SSL certificate corruption error specific to the local Windows environment, which we actively patched by re-routing the CA bundle dynamically.

### Iteration 3: Cross-Component Sensitivity
To satisfy the capstone requirement, we needed to prove the connection between the DCF Valuation layer and the Portfolio Optimizer. We built a 2D Macro-Scenario grid (Bull, Base, Bear) that iteratively reruns the *entire pipeline* to visualize how changing WACC shifts the optimal portfolio weights.

### Iteration 4: The 3-Tab Architectural Upgrade
The single-page app became too cluttered. We evolved the front-end into a professional **Three-Tab Interface**:
1. **Portfolio Optimizer:** The main end-to-end pipeline and efficient frontier.
2. **Risk Adjustment Sandbox:** An isolated laboratory to test purely how Volatility vs. Beta impacts the stock rankings (featuring a custom Plotly Re-ranking visualizer).
3. **Deep Dive DCF Tool:** A standalone financial calculator.

Streamlit `session_state` was utilized to allow the Sandbox tab to "commit" its settings to the global pipeline.
