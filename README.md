# Trader Performance vs Bitcoin Market Sentiment

Institutional-style analysis of the relationship between Hyperliquid trader performance and Bitcoin market sentiment.

## Objective

This project explores how trader outcomes vary across Bitcoin Fear & Greed regimes. It joins daily sentiment classifications with fill-level Hyperliquid trader data, then analyzes realized PnL, win rate, traded volume, side behavior, account concentration, symbol concentration, and strategy implications.

## Deliverables

- `reports/institutional_trader_sentiment_research_deck.pdf`  
  Final presentation-style PDF report.
- `reports/editable_trader_sentiment_research_report.docx`  
  Editable Word report for review and modifications.
- `reports/hyperliquid_trader_sentiment_analysis.xlsx`  
  Supporting Excel workbook with analysis tables.

## Repository Structure

```text
trader-sentiment-analysis/
  data/
    fear_greed_index.csv          # not committed by default
    historical_data.csv           # not committed by default
  reports/
    institutional_trader_sentiment_research_deck.pdf
    editable_trader_sentiment_research_report.docx
    hyperliquid_trader_sentiment_analysis.xlsx
  scripts/
    build_trader_sentiment_report.py
    build_trader_sentiment_pdf.py
    build_trader_sentiment_docx.py
  requirements.txt
  README.md
```

## Data

Expected input files:

1. `data/fear_greed_index.csv`
2. `data/historical_data.csv`

The raw data files are ignored in `.gitignore` because trader data can be large and sensitive. If required for submission, upload them separately or document the source.

You can also point the scripts to another location:

```powershell
$env:FEAR_GREED_CSV="D:\path\to\fear_greed_index.csv"
$env:HISTORICAL_DATA_CSV="D:\path\to\historical_data.csv"
python scripts\build_trader_sentiment_pdf.py
```

## How To Reproduce

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the Excel workbook:

```bash
python scripts/build_trader_sentiment_report.py
```

Generate the PDF deck:

```bash
python scripts/build_trader_sentiment_pdf.py
```

Generate the editable DOCX:

```bash
python scripts/build_trader_sentiment_docx.py
```

## Methodology Summary

- Trader timestamps are parsed from `Timestamp IST`.
- The join key is calendar date in IST.
- Sentiment classification comes from the Bitcoin Fear & Greed dataset.
- Trader performance is measured using `Closed PnL`.
- Normalized efficiency is calculated as `Closed PnL / Size USD * 1,000`.
- Unmatched sentiment dates are excluded from sentiment-regime cuts.

## Key Analytical Views

- Sentiment regime scorecard
- PnL efficiency by regime
- Side and direction behavior
- Daily sentiment versus realized PnL
- Top account contribution
- Top symbol contribution
- Stress-day review
- Strategy playbook by sentiment regime

## Notes

This is a research and analytics project only. It is not investment advice.

