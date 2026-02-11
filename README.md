# FAskills

Claude Code plugins for financial analysis.

> **Disclaimer:** This tool is for educational and informational purposes only. It does not constitute financial advice, investment recommendations, or professional guidance of any kind. The analyses generated are AI-simulated perspectives and should not be used as the basis for any investment decisions. Always consult a qualified financial advisor before making investment decisions. Use at your own risk.

## Plugins

### financial-researcher (v2.0.0)

### financial-researcher (v2.1.0)

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
  - Piotroski F-Score (0-9 financial strength)
  - Altman Z-Score (bankruptcy prediction)
  - Beneish M-Score (earnings manipulation detection)
  - **Credit Metrics**: ICR Stress Test, Refinancing Risk, Leverage Ratios
  - Owner Earnings, EVA, DuPont analysis

- **Output**
  - Signal consensus across all 8 analysts
  - Individual price targets and confidence levels
  - Risk matrix and key concerns
  - Full markdown report + JSON saved to `reports/`

## Installation

1. Clone this repo
2. Configure MCP servers in `.mcp.json` with your API keys:
   - `FINANCIAL_DATASETS_API_KEY` - [financialdatasets.ai](https://financialdatasets.ai)
   - `TAVILY_API_KEY` - [tavily.com](https://tavily.com)

3. Copy `.env.example` to `.env` and add your API keys

## Structure

```
FAskills/
├── .claude-plugin/              # Marketplace config
├── .mcp.json                    # MCP server definitions
├── CLAUDE.md                    # Project instructions
└── financial-researcher/        # The plugin
    ├── .claude-plugin/          # Plugin config
    ├── SKILL.md                 # Main skill orchestration
    ├── experts/                 # 7 investor prompts
    ├── processing/              # Python metrics (Piotroski, Altman, Beneish)
    ├── references/              # DRIVER methodology
    ├── reports/                 # Generated analyses
    └── templates/               # Output schemas
```

## Testing

Test the Python processing layer:
```bash
cd financial-researcher
python -m processing.test_pipeline
```

## License

MIT
