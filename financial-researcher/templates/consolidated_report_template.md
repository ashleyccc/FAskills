# Financial Analysis: {TICKER}

*Generated: {DATE} | Mode: {MODE} | Skill Version: {VERSION}*

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Consensus** | {BULLISH_COUNT} Bullish · {NEUTRAL_COUNT} Neutral · {BEARISH_COUNT} Bearish |
| **Confidence-Weighted Signal** | {WEIGHTED_SIGNAL} ({WEIGHTED_SCORE}%) |
| **Key Agreement** | {AGREEMENT_SUMMARY} |
| **Primary Divergence** | {DIVERGENCE_SUMMARY} |
| **Current Price** | ${CURRENT_PRICE} |
| **Consensus Price Target** | {CONSENSUS_TARGET} |

### The Bull Case ({BULLISH_COUNT} experts)

{BULL_CASE_SUMMARY}

**Supporting experts:** {BULLISH_EXPERTS}

### The Bear Case ({BEARISH_COUNT} experts)

{BEAR_CASE_SUMMARY}

**Supporting experts:** {BEARISH_EXPERTS}

### The Cautious View ({NEUTRAL_COUNT} experts)

{NEUTRAL_CASE_SUMMARY}

**Supporting experts:** {NEUTRAL_EXPERTS}

---

## Signal Overview

```
Signal Distribution:
Bullish  {BULLISH_BAR} {BULLISH_COUNT} ({BULLISH_PCT}%)
Neutral  {NEUTRAL_BAR} {NEUTRAL_COUNT} ({NEUTRAL_PCT}%)
Bearish  {BEARISH_BAR} {BEARISH_COUNT} ({BEARISH_PCT}%)
```

### Confidence by Expert

| Expert | Signal | Confidence | Key Insight |
|--------|--------|------------|-------------|
{EXPERT_SIGNAL_TABLE}

---

## Expert Analyses

<!-- Each expert section below follows this structure -->

{FOR_EACH_EXPERT}

---

### {EXPERT_DISPLAY_NAME}

**Signal:** {SIGNAL_EMOJI} {SIGNAL} | **Confidence:** {CONFIDENCE}%

> **Thesis:** {THESIS}

#### Forward Outlook

| Aspect | Assessment |
|--------|------------|
| **Prediction** | {PREDICTION} |
| **Timeline** | {TIMELINE} |
| **Price Target** | {PRICE_TARGET} |
| **Catalyst** | {CATALYST} |

#### Analysis Breakdown

{ANALYSIS_SECTIONS}

#### Risk Assessment

**Key Risks Identified:**
{KEY_RISKS_LIST}

**What Would Change This View:**
{CHANGE_CONDITIONS_LIST}

#### Holdings Context

| Metric | Value |
|--------|-------|
| **Current Position** | {CURRENT_POSITION} |
| **Recent Changes** | {RECENT_CHANGES} |
| **Signal from Actions** | {SIGNAL_FROM_ACTIONS} |

#### Entry/Exit Levels

- **Would buy aggressively at:** {WOULD_BUY_AT}
- **Would start selling at:** {WOULD_SELL_AT}

#### Private Assessment

> *{PRIVATE_ASSESSMENT}*

{END_FOR_EACH}

---

## Consolidation

### Agreement Matrix

| Theme | {EXPERT_HEADERS} |
|-------|{HEADER_DIVIDERS}|
{AGREEMENT_MATRIX_ROWS}

Legend: ✓ = Mentioned positively | ✗ = Mentioned as concern | · = Not mentioned

### Key Themes

**Points of Agreement ({AGREEMENT_COUNT} themes):**
{AGREEMENT_THEMES_LIST}

**Points of Divergence ({DIVERGENCE_COUNT} themes):**
{DIVERGENCE_THEMES_LIST}

### All Flagged Risks (Deduplicated)

{NUMBERED_RISKS_LIST}

### Price Target Summary

| Expert | Buy At | Target | Sell At |
|--------|--------|--------|---------|
{PRICE_TARGET_TABLE}

**Consensus Range:** Buy below {CONSENSUS_BUY} | Target {CONSENSUS_TARGET} | Sell above {CONSENSUS_SELL}

---

## Data Sources

| Source | Details |
|--------|---------|
| **Financial Data** | financialdatasets.ai (retrieved {DATA_DATE}) |
| **News Context** | Tavily API (last {NEWS_DAYS} days) |
| **SEC Filings** | {FILINGS_LIST} |
| **13-F Holdings** | {HOLDINGS_DATES} |

---

## Methodology Notes

This analysis was generated using the DRIVER Framework:

1. **[DISCOVER]** Gathered financial data, news, and 13-F holdings
2. **[REPRESENT]** Planned analysis approach and expert dispatch
3. **[IMPLEMENT]** Ran 7 expert analyses in parallel
4. **[VALIDATE]** Cross-checked signals and identified contradictions
5. **[EVOLVE]** Consolidated insights while preserving all individual analyses
6. **[REFLECT]** Generated this report and saved JSON output

**Important:** Each expert forms their own independent thesis. There is no debate or consensus-seeking between experts. Divergences represent genuine differences in investment philosophy and are valuable signal, not noise.

---

*Analysis by financial-researcher skill v{VERSION} | DRIVER Framework*
*For internal use only - not investment advice*
