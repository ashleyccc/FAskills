# Financial Researcher

## Structure

```
financial-researcher/
├── .claude-plugin/plugin.json   # Plugin configuration
├── SKILL.md                     # Main skill orchestration (v2.0.0)
├── experts/                     # 7 investor prompts
├── processing/                  # Python metrics layer
├── references/                  # DRIVER methodology
├── reports/                     # Output directory
└── templates/                   # Output schemas
```

## Rules

- SKILL.md controls orchestration. Read fully before editing.
- Python processing layer calculates metrics (Piotroski, Altman, Beneish). Claude does analysis.
- Test processing layer: `python -m processing.test_pipeline`

## Key Files

- `processing/metrics_calculator.py` - Piotroski, Altman, Beneish, etc.
- `processing/orchestrator.py` - `run_analysis()` entry point
- `experts/*.md` - Individual investor analysis prompts
