# /driver:define

## Project Objective
The goal is to build an AI-driven, end-to-end Value Portfolio Optimizer called the **DRIVER Framework**. This application must integrate a Discounted Cash Flow (DCF) valuation tool with a modern risk-adjusted Mean-Variance Portfolio Optimizer. The final deliverable must be a highly interactive, multi-tab Streamlit dashboard deployed for a capstone finance class.

## Core Requirements
1. **DCF Valuation Engine:** Pull live financial data from Yahoo Finance to calculate Free Cash Flow, WACC, Margin of Safety, and Intrinsic Value. 
2. **Risk-Adjusted Preference Layer:** Intercept the DCF-screened universe and scale the risk using a dynamic blend of Volatility and Beta, controlled by an "Alpha" slider.
3. **Portfolio Optimizer:** Use SLSQP optimization to generate a portfolio that either Maximizes the Sharpe Ratio or Minimizes Variance, bounded by maximum position weights.
4. **Cross-Component Sensitivity:** Prove how varying macroeconomic assumptions (WACC & Terminal Growth) actively shifts stock selection and alters the final optimal portfolio weights.

## Constraints & Technology
- Python, Streamlit, Pandas, NumPy, yfinance, SciPy, Plotly.
- Must execute on real live data.
- Must have a clean, professional, and intuitive user interface using a multi-tab architecture.
- All code must be pushed to the `FAskills` GitHub repository.
