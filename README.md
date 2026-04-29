# DRIVER Framework: Value-Based Portfolio Optimizer

> **Disclaimer:** This tool is for educational and informational purposes only. It does not constitute financial advice, investment recommendations, or professional guidance of any kind. The analyses generated are AI-simulated perspectives and should not be used as the basis for any investment decisions. Always consult a qualified financial advisor before making investment decisions. Use at your own risk.

## Project Description
The **DRIVER Framework** is a fully interactive, end-to-end financial dashboard built in Python and Streamlit. It bridges the gap between fundamental value investing and modern portfolio theory. By automatically pulling live market data from Yahoo Finance, the application screens a universe of stocks using a Discounted Cash Flow (DCF) model, intercepts the results with a highly customizable Risk-Adjusted Preference Layer, and outputs mathematically optimal portfolio weights using SciPy's SLSQP optimizer.

## Project Goals
1. **Automated DCF Valuation:** Eliminate manual modeling by dynamically calculating Free Cash Flow, WACC, and Intrinsic Value for any given stock.
2. **Dynamic Risk-Adjustment:** Allow users to define their own risk philosophy by blending "Pure Valuation" (Margin of Safety) with "Pure Safety" (Volatility and Market Beta).
3. **Advanced Portfolio Optimization:** Empower users to effortlessly shift between Maximizing the Sharpe Ratio or Minimizing Variance to generate actionable portfolio allocations.
4. **Cross-Component Sensitivity:** Visually prove the butterfly effect of finance—demonstrating exactly how a minor shift in a macroeconomic assumption (like Terminal Growth) drastically alters the final optimal portfolio weights.

## Instructions / How to Run

### 1. Installation
Ensure you have Python installed. Clone the repository and install the required dependencies:
```bash
git clone https://github.com/ashleyccc/FAskills.git
cd FAskills
pip install -r requirements.txt
```

### 2. Launch the Application
Start the Streamlit server to launch the interactive dashboard:
```bash
streamlit run app.py
```
This will open the application in your default web browser (typically at `http://localhost:8501`).

### 3. Using the App
- **Tab 1 (Portfolio Optimizer):** View the end-to-end pipeline, adjust global WACC/Growth assumptions, and analyze the Efficient Frontier.
- **Tab 2 (Risk Adjustment Sandbox):** Experiment with custom tickers, isolate risk metrics (Volatility vs. Beta), visualize the Re-ranking effect, and click **"Apply to Main Pipeline"** to commit your strategy.
- **Tab 3 (Deep Dive DCF Tool):** Run granular, individualized DCF sensitivity analyses on single tickers.

---

## Previous Plugins & Methodologies

*The DRIVER Framework methodology artifacts can be found in `driver_define.md`, `driver_evolve.md`, and `driver_reflect.md`.*

### financial-researcher (Legacy Plugin)

8 legendary investors analyze any stock. One command.

```
/financial-researcher AAPL          # Prompts for mode
/financial-researcher NVDA --full   # Full 8-guru analysis (includes CRO)
/financial-researcher TSLA --quick  # Quick metrics only
```

#### Investors
| Investor | Focus |
|----------|-------|
| Warren Buffett | Moats, owner earnings, intrinsic value |
| Ben Graham | Margin of safety, asset-based valuation |
| Peter Lynch | PEG ratio, growth story |
| Cathie Wood | Disruption, TAM, 5-year vision |
| George Soros | Reflexivity, macro regime |
| Ray Dalio | Cycles, debt analysis, stress tests |
| Michael Burry | Forensics, bear case, contrarian signals |
| **Chief Risk Officer** | **Solvency, liquidity, Basel III stress tests** |

#### Features
- **Python Processing Layer** - Pre-calculates institutional-grade metrics:
  - Piotroski F-Score, Altman Z-Score, Beneish M-Score
  - **Credit Metrics**: ICR Stress Test, Refinancing Risk, Leverage Ratios
- **Output**
  - Signal consensus across all 8 analysts
  - Individual price targets and confidence levels

### Structure
```
FAskills/
├── app.py                       # Main Streamlit Dashboard
├── valuation_engine.py          # DCF Modeling Math
├── risk_adjustment.py           # Ranking & Scaling Logic
├── portfolio_optimizer.py       # SciPy SLSQP Optimization
├── data_client.py               # Yahoo Finance Integration
├── driver_*.md                  # DRIVER Methodology Artifacts
└── financial-researcher/        # Legacy Claude Plugin
```

## AI Usage Disclosure & Reflection
This project was developed with the assistance of an advanced AI coding agent (Antigravity). The AI was utilized to scaffold the Streamlit architecture, implement the mathematical optimization algorithms (SciPy SLSQP), and debug environment issues (e.g., SSL certificate bypasses). 

**Reflection:** Using an autonomous agent drastically accelerated the development timeline, allowing me to focus on the high-level financial architecture (e.g., designing the Risk Adjustment Sandbox and defining the Macro-Scenario Sensitivity Grid) rather than getting bogged down in Pandas syntax or Streamlit state management. However, it required strict oversight; I had to explicitly define financial guardrails (like preventing the Gordon Growth Model from breaking when Terminal Growth > WACC) to ensure the AI's code remained mathematically sound. This project demonstrated that AI is a powerful execution engine, but human domain expertise is still fundamentally required to guide the logic and validate the outputs.

## License
MIT
