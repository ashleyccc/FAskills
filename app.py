import streamlit as st
import pandas as pd
import numpy as np
from data_client import fetch_financial_data, fetch_historical_prices
from valuation_engine import screen_stocks, run_dcf, generate_dcf_sensitivity
from risk_adjustment import apply_risk_adjusted_layer
from portfolio_optimizer import optimize_portfolio, generate_efficient_frontier

# Set wide layout and page config
st.set_page_config(page_title="DRIVER Value Portfolio", layout="wide")

st.title("Value-Based Portfolio Optimizer (DRIVER Framework)")
st.markdown("This dashboard implements the **Risk-Adjusted Preference Layer** and portfolio optimization pipeline.")

st.info("**Disclaimer:** This tool is for educational and informational purposes only. It does not constitute financial advice, investment recommendations, or professional guidance of any kind. The analyses generated are AI-simulated perspectives and should not be used as the basis for any investment decisions. Always consult a qualified financial advisor before making investment decisions. Use at your own risk.")

# --- INITIALIZE SESSION STATE ---
if "global_alpha" not in st.session_state:
    st.session_state.global_alpha = 0.5
if "global_risk_metric" not in st.session_state:
    st.session_state.global_risk_metric = "Both"

# Sidebar Controls
st.sidebar.header("Pipeline Parameters")

st.sidebar.subheader("1. DCF Valuation")
min_margin = st.sidebar.slider("Min Margin of Safety (%)", min_value=-100, max_value=100, value=-100, step=5) / 100.0
global_wacc = st.sidebar.slider("Global WACC", min_value=0.05, max_value=0.20, value=0.10, step=0.01)
global_stg = st.sidebar.slider("Global Short-Term Growth", min_value=0.0, max_value=0.50, value=0.05, step=0.01)
global_tg = st.sidebar.slider("Global Terminal Growth", min_value=0.0, max_value=0.05, value=0.02, step=0.01)
if global_tg > 0.03:
    st.sidebar.warning("Warning: Terminal growth > 3% GDP. Assumption may be overly aggressive.")

st.sidebar.subheader("2. Risk-Adjusted Layer")
st.sidebar.info(f"**Current Alpha:** {st.session_state.global_alpha}\n\n**Metric:** {st.session_state.global_risk_metric}\n\n*(Edit in Tab 2)*")
top_n = st.sidebar.number_input("Top N Stocks to Keep", min_value=1, max_value=50, value=15, step=1)

st.sidebar.subheader("3. Portfolio Optimizer")
optimizer_objective = st.sidebar.radio("Optimization Objective", options=["Max Sharpe", "Min Variance"], index=0)
max_weight = st.sidebar.slider("Max Position Weight (%)", min_value=5, max_value=100, value=20, step=1) / 100.0


# Universe (Hardcoded for prototype speed, ideally dynamic)
DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "DIS",
    "BAC", "HD", "CRM", "XOM", "KO", "PEP", "COST", "MCD",
    "ABBV", "CVX", "TMO", "CSCO", "ACN", "ABT", "LIN"
]

@st.cache_data(ttl=3600)
def load_data(tickers, cache_buster=1):
    stock_data = {}
    for t in tickers:
        data = fetch_financial_data(t)
        if data:
            stock_data[t] = data
    historical_prices = fetch_historical_prices(tickers, period="2y")
    return stock_data, historical_prices

with st.spinner("Fetching data..."):
    stock_data, historical_prices = load_data(DEFAULT_UNIVERSE, cache_buster=2)

# Pipeline Execution Function
def run_pipeline(objective="Max Sharpe", wacc=0.10, stg=0.05, tg=0.02):
    current_alpha = st.session_state.global_alpha
    risk_metric = st.session_state.global_risk_metric
    
    # 1. Screen
    screened_df = screen_stocks(stock_data, min_margin_of_safety=min_margin, wacc=wacc, short_term_growth=stg, terminal_growth=tg)
    if screened_df.empty:
        return pd.DataFrame(), {}, pd.DataFrame(), {}
        
    # 2. Risk Adjustment
    risk_adj_df = apply_risk_adjusted_layer(screened_df, historical_prices, alpha=current_alpha, top_n=top_n, risk_metric_choice=risk_metric)
    
    if risk_adj_df.empty:
        return pd.DataFrame(), {}, pd.DataFrame(), {}
        
    # 3. Optimize
    tickers_to_optimize = risk_adj_df["Ticker"].tolist()
    opt_res = optimize_portfolio(tickers_to_optimize, historical_prices, max_weight=max_weight, objective=objective)
    optimal_weights = opt_res.get("weights", {})
    
    # Append weights to dataframe for display
    risk_adj_df["Final Optimizer Weight"] = risk_adj_df["Ticker"].map(optimal_weights).fillna(0)
    
    # Format for display
    display_df = risk_adj_df[[
        "Ticker", "Margin of Safety", "Raw Volatility", "Raw Beta", 
        "Min-Max Valuation Score", "Min-Max Safety Score", 
        "Final Blended Score", "Pipeline Rank", "Final Optimizer Weight"
    ]].copy()
    
    display_df["Margin of Safety"] = (display_df["Margin of Safety"] * 100).map("{:.1f}%".format)
    display_df["Final Optimizer Weight"] = (display_df["Final Optimizer Weight"] * 100).map("{:.1f}%".format)
    for col in ["Raw Volatility", "Raw Beta", "Min-Max Valuation Score", "Min-Max Safety Score", "Final Blended Score"]:
        display_df[col] = display_df[col].map("{:.4f}".format)
        
    return display_df, optimal_weights, risk_adj_df, opt_res

tab1, tab2, tab3 = st.tabs(["Portfolio Optimizer", "Risk Adjustment Sandbox", "Deep Dive DCF Tool"])

with tab1:
    st.header("Pipeline Dependency Chain")

display_df, current_weights, risk_adj_df, opt_res = run_pipeline(optimizer_objective, global_wacc, global_stg, global_tg)

if display_df.empty:
    st.warning("No stocks passed the initial DCF screen or data is missing.")
elif "error" in opt_res:
    st.error(opt_res["error"])
else:
    st.subheader(f"Optimal Portfolio Performance ({optimizer_objective})")
    st.caption("Note: Expected Return is a mathematical estimate based on historical covariance and is not a guaranteed value.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Expected Return (Annual)", f"{opt_res.get('expected_return', 0)*100:.2f}%")
    m2.metric("Expected Risk (Volatility)", f"{opt_res.get('expected_volatility', 0)*100:.2f}%")
    m3.metric("Sharpe Ratio", f"{opt_res.get('sharpe_ratio', 0):.2f}")
    
    st.dataframe(display_df, use_container_width=True)
    
    import plotly.express as px
    
    st.subheader("Visualizing the Bridge")
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter Plot: Valuation vs Safety
        # Size by weight, color by Final Score
        # Ensure sizes are strictly positive for plotly (replace 0 with a tiny amount)
        sizes = [max(0.01, w) for w in risk_adj_df["Final Optimizer Weight"]]
        fig_scatter = px.scatter(
            risk_adj_df, 
            x="Min-Max Valuation Score", 
            y="Min-Max Safety Score", 
            color="Final Blended Score",
            size=sizes,
            hover_name="Ticker",
            title="Valuation vs. Safety Trade-off (Bubble Size = Portfolio Weight)",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True, key="scatter_chart")
        
    with col2:
        # Donut Chart: Final Portfolio Weights
        pie_df = risk_adj_df[risk_adj_df["Final Optimizer Weight"] > 0.001]
        if not pie_df.empty:
            fig_pie = px.pie(
                pie_df, 
                values="Final Optimizer Weight", 
                names="Ticker", 
                title=f"Optimal Portfolio Allocation (Max Pos: {max_weight*100:.0f}%)",
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")
        else:
            st.info("No weights allocated by the optimizer.")
            
    # Efficient Frontier
    st.subheader("Efficient Frontier")
    st.markdown("Simulating 1,500 random portfolio allocations to visualize the risk-return tradeoff.")
    tickers_to_optimize = risk_adj_df["Ticker"].tolist()
    
    with st.spinner("Generating Efficient Frontier..."):
        ef_df = generate_efficient_frontier(tickers_to_optimize, historical_prices)
        
    if not ef_df.empty:
        import plotly.graph_objects as go
        
        fig_ef = px.scatter(
            ef_df, x="Volatility", y="Return", color="Sharpe Ratio",
            title="Efficient Frontier (Random Portfolios)",
            labels={"Volatility": "Expected Risk (Annual Volatility)", "Return": "Expected Return"},
            color_continuous_scale="Viridis",
            opacity=0.6
        )
        
        # Overlay the actual Optimal Portfolio
        fig_ef.add_trace(go.Scatter(
            x=[opt_res.get('expected_volatility', 0)],
            y=[opt_res.get('expected_return', 0)],
            mode='markers',
            marker=dict(color='red', size=15, symbol='star'),
            name=f'Optimal ({optimizer_objective})'
        ))
        
        fig_ef.layout.xaxis.tickformat = ',.1%'
        fig_ef.layout.yaxis.tickformat = ',.1%'
        st.plotly_chart(fig_ef, use_container_width=True, key="ef_chart")
# --- SENSITIVITY ANALYSIS ---
st.header("Cross-Component Sensitivity: Macro Scenarios")
st.markdown("Comparing optimal portfolio weights across different **WACC and Terminal Growth** scenarios to see how valuation impacts stock selection.")

macro_scenarios = {
    "Bull (WACC -2%, TG +1%)": {"wacc": max(0.05, global_wacc - 0.02), "tg": global_tg + 0.01},
    "Base (User Assumptions)": {"wacc": global_wacc, "tg": global_tg},
    "Bear (WACC +2%, TG -1%)": {"wacc": global_wacc + 0.02, "tg": max(0.0, global_tg - 0.01)}
}

comparison_dict = {}

for name, params in macro_scenarios.items():
    _, w, _, _ = run_pipeline(objective=optimizer_objective, wacc=params["wacc"], stg=global_stg, tg=params["tg"])
    comparison_dict[name] = w
    
# Aggregate all tickers that appeared in any of the portfolios
all_tickers = set()
for w_dict in comparison_dict.values():
    all_tickers.update(w_dict.keys())

sensitivity_data = []
for t in sorted(list(all_tickers)):
    row = {"Ticker": t}
    for name in macro_scenarios.keys():
        weight = comparison_dict[name].get(t, 0.0)
        row[f"{name} Weight"] = f"{weight * 100:.1f}%"
    sensitivity_data.append(row)

sens_df_opt = pd.DataFrame(sensitivity_data)
st.dataframe(sens_df_opt, use_container_width=True)

st.subheader("Visualizing Sensitivity: Allocation Shifts")
plot_data = []
for index, row in sens_df_opt.iterrows():
    ticker = row["Ticker"]
    for name in macro_scenarios.keys():
        weight_str = row[f"{name} Weight"]
        weight_val = float(weight_str.replace('%', '')) / 100.0
        if weight_val > 0.001:
            plot_data.append({"Ticker": ticker, "Scenario": name, "Weight": weight_val})

plot_df = pd.DataFrame(plot_data)
if not plot_df.empty:
    fig_bar = px.bar(
        plot_df, 
        x="Ticker", 
        y="Weight", 
        color="Scenario", 
        barmode="group",
        title="Portfolio Weights across Macro Economic Scenarios (DCF Assumptions)"
    )
    fig_bar.layout.yaxis.tickformat = ',.0%'
    st.plotly_chart(fig_bar, use_container_width=True, key="macro_bar_chart")

with tab2:
    st.header("Risk Adjustment Sandbox")
    st.markdown("Isolate the risk layer to experiment with different risk metrics and Alpha blends before committing them to the main pipeline.")
    st.info("Note: The Risk-Adjusted Score represents **Safety**. A higher score means the stock is mathematically safer based on your metric choice.")
    
    col_input, col_controls = st.columns(2)
    
    with col_input:
        universe_source = st.radio("Universe Source", ["Use Tab 1 DCF Screened Names", "Custom Ticker List"])
        custom_tickers = ""
        if universe_source == "Custom Ticker List":
            custom_tickers = st.text_input("Enter Tickers (comma separated)", "AAPL, MSFT, JNJ, V, XOM")
            
    with col_controls:
        sandbox_metric = st.selectbox("Risk Metric Choice", ["Both", "Volatility Only", "Beta Only"], index=["Both", "Volatility Only", "Beta Only"].index(st.session_state.global_risk_metric))
        sandbox_alpha = st.slider("Sandbox Alpha (Valuation vs Safety)", min_value=0.0, max_value=1.0, value=st.session_state.global_alpha, step=0.1)
        
        if st.button("Apply to Main Pipeline", type="primary"):
            st.session_state.global_alpha = sandbox_alpha
            st.session_state.global_risk_metric = sandbox_metric
            st.rerun()
            
    st.divider()
    
    # Get Sandbox Data
    sandbox_screened = pd.DataFrame()
    sandbox_hist_prices = historical_prices
    
    if universe_source == "Use Tab 1 DCF Screened Names":
        # We need the base screened df from Tab 1
        sandbox_screened = screen_stocks(stock_data, min_margin_of_safety=min_margin, wacc=global_wacc, short_term_growth=global_stg, terminal_growth=global_tg)
    else:
        tickers_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
        rows = []
        new_tickers = []
        for t in tickers_list:
            if t in stock_data:
                rows.append({"Ticker": t, "Margin of Safety": stock_data[t].get("margin_of_safety", 0.0), "Raw Beta": stock_data[t].get("beta", 1.0)})
            else:
                try:
                    data = fetch_financial_data(t)
                    if data:
                        rows.append({"Ticker": t, "Margin of Safety": 0.0, "Raw Beta": data.get("beta", 1.0)})
                        new_tickers.append(t)
                except:
                    pass
        sandbox_screened = pd.DataFrame(rows)
        
        if new_tickers:
            new_hist = fetch_historical_prices(new_tickers, period="2y")
            if not new_hist.empty:
                sandbox_hist_prices = pd.concat([historical_prices, new_hist], axis=1)
        
    if not sandbox_screened.empty:
        # Run Sandbox Risk Layer
        sandbox_res = apply_risk_adjusted_layer(sandbox_screened, sandbox_hist_prices, alpha=sandbox_alpha, top_n=50, risk_metric_choice=sandbox_metric)
        
        if not sandbox_res.empty:
            st.subheader("Sandbox Risk Metrics")
            # Create a display copy to format floats
            s_disp = sandbox_res.copy()
            for col in ["Raw Volatility", "Raw Beta", "Min-Max Valuation Score", "Min-Max Safety Score", "Final Blended Score"]:
                if col in s_disp.columns:
                    s_disp[col] = s_disp[col].map("{:.4f}".format)
                    
            display_cols = [c for c in ["Ticker", "Raw Volatility", "Raw Beta", "Min-Max Valuation Score", "Min-Max Safety Score", "Final Blended Score", "Pipeline Rank"] if c in s_disp.columns]
            st.dataframe(s_disp[display_cols], use_container_width=True)
            
            # Re-Ranking Visualization
            st.subheader("Visualizing the Re-ranking Effect")
            st.markdown("How does your Alpha preference shift the ranking compared to a **Pure Valuation (Alpha=1.0)** strategy?")
            
            pure_val_res = apply_risk_adjusted_layer(sandbox_screened, sandbox_hist_prices, alpha=1.0, top_n=50, risk_metric_choice=sandbox_metric)
            
            if not pure_val_res.empty:
                compare_df = pd.merge(
                    sandbox_res[["Ticker", "Pipeline Rank"]].rename(columns={"Pipeline Rank": f"Current Rank (Alpha={sandbox_alpha})"}),
                    pure_val_res[["Ticker", "Pipeline Rank"]].rename(columns={"Pipeline Rank": "Pure Valuation Rank (Alpha=1.0)"}),
                    on="Ticker"
                )
                
                import plotly.graph_objects as go
                fig_rank = go.Figure()
                for i, row in compare_df.iterrows():
                    fig_rank.add_trace(go.Scatter(
                        x=["Pure Valuation (Alpha=1.0)", f"Current Alpha ({sandbox_alpha})"],
                        y=[row["Pure Valuation Rank (Alpha=1.0)"], row[f"Current Rank (Alpha={sandbox_alpha})"]],
                        mode="lines+markers+text",
                        name=row["Ticker"],
                        text=[row["Ticker"], row["Ticker"]],
                        textposition="top center"
                    ))
                fig_rank.update_yaxes(autorange="reversed", title="Pipeline Rank (Lower is Better)")
                fig_rank.update_layout(title="Stock Rank Shifts: Valuation vs. Safety Blend")
                st.plotly_chart(fig_rank, use_container_width=True, key="rank_shift_chart")
        else:
            st.warning("No data generated in sandbox.")
    else:
        st.warning("Sandbox universe is empty. Try a wider Margin of Safety or enter valid tickers.")

with tab3:
    st.header("Individual Stock Deep Dive (DCF Tool)")
    st.markdown("Satisfying Project 1 Requirements: Retrieve financials, calculate intrinsic value, adjust assumptions, and generate a sensitivity matrix.")
    
    ticker_input = st.text_input("Enter Stock Ticker", value="AAPL")
    
    col_wacc, col_growth, col_term = st.columns(3)
    user_wacc = col_wacc.slider("WACC (Discount Rate)", min_value=0.05, max_value=0.20, value=0.10, step=0.01)
    user_growth = col_growth.slider("Short-Term Growth Rate", min_value=0.0, max_value=0.50, value=0.05, step=0.01)
    user_term = col_term.slider("Terminal Growth Rate", min_value=0.0, max_value=0.05, value=0.02, step=0.01)
    
    if user_term > 0.03:
        st.warning("Warning: Terminal growth exceeds standard long-run GDP growth (3%).")
    
    if st.button("Run DCF Analysis"):
        with st.spinner(f"Fetching data for {ticker_input}..."):
            fin_data = fetch_financial_data(ticker_input.upper())
            
        if fin_data:
            # Run DCF
            dcf_res = run_dcf(
                fcf=fin_data["fcf"], 
                shares_outstanding=fin_data["shares_outstanding"], 
                current_price=fin_data["current_price"],
                discount_rate=user_wacc,
                short_term_growth=user_growth,
                terminal_growth_rate=user_term
            )
            
            if dcf_res:
                if "error" in dcf_res:
                    st.error(dcf_res["error"])
                else:
                    if "warning" in dcf_res:
                        st.warning(dcf_res["warning"])
                        
                    st.subheader(f"Valuation Outputs for {ticker_input.upper()}")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Current Price", f"${fin_data['current_price']:.2f}")
                
                margin_color = "normal" if dcf_res['margin_of_safety'] > 0 else "inverse"
                m2.metric("Per-Share Intrinsic Value", f"${dcf_res['intrinsic_value']:.2f}", f"{dcf_res['margin_of_safety']*100:.1f}% Margin", delta_color=margin_color)
                
                m3.metric("Equity Value", f"${dcf_res['equity_value']:,.0f}")
                m4.metric("Enterprise Value", f"${dcf_res['enterprise_value']:,.0f}")
                
                st.subheader("DCF Sensitivity Analysis")
                st.markdown("Intrinsic Value changes across WACC and Growth Rate combinations:")
                dcf_sens_df = generate_dcf_sensitivity(
                    fcf=fin_data["fcf"], 
                    shares_outstanding=fin_data["shares_outstanding"], 
                    current_price=fin_data["current_price"],
                    base_wacc=user_wacc,
                    base_growth=user_growth,
                    terminal_growth=user_term
                )
                st.dataframe(dcf_sens_df, use_container_width=True)
            else:
                st.error("Failed to calculate DCF. Invalid financial data.")
        else:
            st.error("Could not retrieve data for the ticker.")
