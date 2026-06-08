# 🚀 Trader Performance vs Bitcoin Market Sentiment

### Institutional-Style Quantitative Research on Hyperliquid Trader Behavior

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-green)
![Research](https://img.shields.io/badge/Research-Quantitative-orange)
![Finance](https://img.shields.io/badge/Domain-Crypto%20Markets-purple)
![Status](https://img.shields.io/badge/Status-Completed-success)

---

## 📖 Overview

This project investigates how trader performance changes across different Bitcoin market sentiment regimes using the **Bitcoin Fear & Greed Index** and **Hyperliquid trading activity data**.

The objective is to determine whether trader profitability, efficiency, trading volume, and directional behavior vary during periods of:

* 😱 Extreme Fear
* 😨 Fear
* 😐 Neutral
* 😊 Greed
* 🚀 Extreme Greed

The analysis follows an institutional research approach commonly used by hedge funds, quantitative trading firms, and market intelligence teams.

---

## 🎯 Research Questions

* Do traders perform better during fear or greed markets?
* How does profitability change across sentiment regimes?
* Does trading activity increase during extreme market conditions?
* Which trader groups contribute most to profits?
* Which assets dominate trading activity?
* Can sentiment be used as a practical trading signal?

---

## 📊 Key Metrics Analyzed

| Metric               | Description                     |
| -------------------- | ------------------------------- |
| Realized PnL         | Closed profit and loss          |
| Win Rate             | Percentage of profitable trades |
| Trading Volume       | Total USD traded                |
| Trader Concentration | Contribution of top accounts    |
| Symbol Concentration | Contribution of top assets      |
| Trade Direction      | Long vs Short behavior          |
| PnL Efficiency       | PnL generated per $1000 traded  |

---

## 🏗️ Project Architecture

```text
Fear & Greed Index
        │
        ▼
Sentiment Classification
        │
        ▼
Date-Level Join
        │
        ▼
Hyperliquid Trade Data
        │
        ▼
Performance Analytics
        │
        ▼
Research Reports & Insights
```

---

## 📂 Repository Structure

```text
trader-sentiment-analysis/
│
├── data/
│   ├── fear_greed_index.csv
│   └── historical_data.csv
│
├── reports/
│   ├── institutional_trader_sentiment_research_deck.pdf
│   ├── editable_trader_sentiment_research_report.docx
│   └── hyperliquid_trader_sentiment_analysis.xlsx
│
├── scripts/
│   ├── build_trader_sentiment_report.py
│   ├── build_trader_sentiment_pdf.py
│   └── build_trader_sentiment_docx.py
│
├── requirements.txt
└── README.md
```

---

## 🔬 Methodology

### Data Sources

#### Bitcoin Fear & Greed Index

Used to classify market sentiment into five psychological regimes:

| Score Range | Classification |
| ----------- | -------------- |
| 0–24        | Extreme Fear   |
| 25–44       | Fear           |
| 45–54       | Neutral        |
| 55–74       | Greed          |
| 75–100      | Extreme Greed  |

#### Hyperliquid Trading Data

Includes:

* Account activity
* Trade direction
* Position size
* Closed PnL
* Trading timestamps
* Asset traded

---

### Data Processing Pipeline

1. Parse trade timestamps
2. Convert timestamps to trading dates
3. Merge trades with sentiment data
4. Aggregate trader statistics
5. Compute profitability metrics
6. Generate institutional-style reports

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/trader-sentiment-analysis.git
cd trader-sentiment-analysis
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Generate Excel Analysis

```bash
python scripts/build_trader_sentiment_report.py
```

### Generate PDF Research Deck

```bash
python scripts/build_trader_sentiment_pdf.py
```

### Generate Editable DOCX Report

```bash
python scripts/build_trader_sentiment_docx.py
```

---

## 📈 Analytical Views Produced

* Sentiment Regime Scorecard
* PnL Efficiency Analysis
* Daily Performance Trends
* Trader Concentration Analysis
* Symbol Concentration Analysis
* Long vs Short Behavior
* Stress-Day Analysis
* Sentiment-Based Trading Playbook

---

## 💡 Example Insights

The framework enables discovery of patterns such as:

* Traders becoming more active during extreme sentiment periods.
* Profitability clustering around specific market regimes.
* Increased concentration among top-performing accounts.
* Certain assets outperforming under specific sentiment conditions.

---

## 📑 Deliverables

### 📊 Research Deck

Professional presentation-style PDF containing:

* Executive Summary
* Key Findings
* Visualizations
* Strategic Recommendations

### 📈 Excel Workbook

Detailed quantitative outputs including:

* Aggregated metrics
* Pivot summaries
* Statistical breakdowns

### 📝 Editable Report

Comprehensive Word document suitable for:

* Client presentations
* Internal research
* Portfolio submissions

---

## 🛠️ Technologies Used

<p align="left">
  <img src="https://skillicons.dev/icons?i=python,vscode,git,github" />
</p>

* Python
* Pandas
* NumPy
* OpenPyXL
* ReportLab
* Python-Docx

---

## 📚 Future Improvements

* Machine Learning sentiment prediction
* Hyperliquid API integration
* Interactive Streamlit dashboard
* Time-series forecasting
* Trader clustering and segmentation
* Automated report generation pipeline

---

## ⚠️ Disclaimer

This project is intended solely for research, educational, and analytical purposes.

Nothing in this repository should be interpreted as financial, trading, or investment advice.

---

## 👨‍💻 Author

### Sanket Bachhav

AI Engineer • Data Science • Machine Learning • Quantitative Analytics

If you found this project interesting, consider giving it a ⭐ on GitHub.
