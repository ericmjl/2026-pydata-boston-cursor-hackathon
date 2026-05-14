# Submission: UK VAT counterfactual (Online Retail)

Interactive Marimo notebook comparing actual monthly revenue to a seasonality + growth benchmark around the UK VAT change (4 January 2011).

## Run

From this directory:

```bash
uvx marimo edit --sandbox --no-token hackathon-notebook.py
```

Data lives in `data/OnlineRetail.csv` next to the notebook.

## Files

- `hackathon-notebook.py` — Marimo app (Polars + Plotly).
- `data/OnlineRetail.csv` — UCI Online Retail sample.
- `scripts/` — Optional helpers used while authoring via marimo-pair (`execute-code.sh`); not required to run the notebook.
