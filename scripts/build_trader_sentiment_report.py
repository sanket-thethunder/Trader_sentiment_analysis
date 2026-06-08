from __future__ import annotations

import os
import math
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


ROOT = Path.cwd()
DEFAULT_SOURCE_DIR = Path(r"D:\companies tast\internshala primetrade ai")
LOCAL_DATA_DIR = ROOT / "data"
FEAR_GREED = Path(os.getenv("FEAR_GREED_CSV", LOCAL_DATA_DIR / "fear_greed_index.csv"))
TRADES = Path(os.getenv("HISTORICAL_DATA_CSV", LOCAL_DATA_DIR / "historical_data.csv"))
if not FEAR_GREED.exists():
    FEAR_GREED = DEFAULT_SOURCE_DIR / "fear_greed_index.csv"
if not TRADES.exists():
    TRADES = DEFAULT_SOURCE_DIR / "historical_data.csv"
OUT_DIR = Path(os.getenv("OUTPUT_DIR", ROOT / "outputs" / "trader_sentiment_analysis"))
OUT_FILE = OUT_DIR / "hyperliquid_trader_sentiment_analysis.xlsx"

SENTIMENT_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
SENTIMENT_SCORE = {
    "Extreme Fear": 1,
    "Fear": 2,
    "Neutral": 3,
    "Greed": 4,
    "Extreme Greed": 5,
}

COLORS = {
    "navy": "17324D",
    "blue": "2F75B5",
    "teal": "1F9A8A",
    "green": "70AD47",
    "amber": "F4B183",
    "red": "C00000",
    "light_blue": "DDEBF7",
    "light_teal": "DDEEEB",
    "light_green": "E2F0D9",
    "light_amber": "FFF2CC",
    "light_red": "FCE4D6",
    "gray": "F2F2F2",
    "dark_gray": "595959",
    "white": "FFFFFF",
}


def money(x: float) -> str:
    if pd.isna(x):
        return ""
    sign = "-" if x < 0 else ""
    x = abs(float(x))
    if x >= 1_000_000:
        return f"{sign}${x / 1_000_000:,.2f}M"
    if x >= 1_000:
        return f"{sign}${x / 1_000:,.1f}K"
    return f"{sign}${x:,.0f}"


def pct(x: float) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x) * 100:.1f}%"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sentiment = pd.read_csv(FEAR_GREED)
    sentiment["date"] = pd.to_datetime(sentiment["date"], errors="coerce").dt.date
    sentiment["classification"] = sentiment["classification"].astype(str).str.strip()
    sentiment["sentiment_score"] = sentiment["classification"].map(SENTIMENT_SCORE)
    sentiment = sentiment.dropna(subset=["date", "classification"])

    trades = pd.read_csv(TRADES)
    rename = {
        "Account": "account",
        "Coin": "coin",
        "Execution Price": "execution_price",
        "Size Tokens": "size_tokens",
        "Size USD": "size_usd",
        "Side": "side",
        "Timestamp IST": "timestamp_ist",
        "Start Position": "start_position",
        "Direction": "direction",
        "Closed PnL": "closed_pnl",
        "Fee": "fee",
        "Timestamp": "timestamp",
    }
    trades = trades.rename(columns=rename)
    for col in ["execution_price", "size_tokens", "size_usd", "start_position", "closed_pnl", "fee"]:
        trades[col] = pd.to_numeric(trades[col], errors="coerce")
    trades["trade_dt_ist"] = pd.to_datetime(trades["timestamp_ist"], format="%d-%m-%Y %H:%M", errors="coerce")
    trades["date"] = trades["trade_dt_ist"].dt.date
    trades["side"] = trades["side"].astype(str).str.upper().str.strip()
    trades["direction"] = trades["direction"].astype(str).str.strip()
    trades = trades.dropna(subset=["date", "closed_pnl", "size_usd"])

    merged = trades.merge(
        sentiment[["date", "value", "classification", "sentiment_score"]],
        on="date",
        how="left",
    )
    merged["classification"] = merged["classification"].fillna("Unmatched")
    merged["is_win"] = merged["closed_pnl"] > 0
    merged["is_loss"] = merged["closed_pnl"] < 0
    merged["abs_pnl"] = merged["closed_pnl"].abs()
    merged["pnl_per_1k_usd"] = np.where(merged["size_usd"] != 0, merged["closed_pnl"] / merged["size_usd"] * 1000, np.nan)
    merged["hour"] = merged["trade_dt_ist"].dt.hour
    return sentiment, trades, merged


def metric_frame(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = df.groupby(group_cols, dropna=False).agg(
        trades=("closed_pnl", "size"),
        accounts=("account", "nunique"),
        symbols=("coin", "nunique"),
        volume_usd=("size_usd", "sum"),
        total_pnl=("closed_pnl", "sum"),
        avg_pnl=("closed_pnl", "mean"),
        median_pnl=("closed_pnl", "median"),
        win_rate=("is_win", "mean"),
        avg_pnl_per_1k=("pnl_per_1k_usd", "mean"),
        total_fee=("fee", "sum"),
        avg_trade_size=("size_usd", "mean"),
    ).reset_index()
    grouped["profit_factor"] = grouped.apply(
        lambda r: np.nan if df.empty else np.nan, axis=1
    )

    pf = []
    for _, row in grouped[group_cols].iterrows():
        sub = df
        for c in group_cols:
            sub = sub[sub[c] == row[c]]
        gains = sub.loc[sub["closed_pnl"] > 0, "closed_pnl"].sum()
        losses = -sub.loc[sub["closed_pnl"] < 0, "closed_pnl"].sum()
        pf.append(gains / losses if losses else np.nan)
    grouped["profit_factor"] = pf
    return grouped


def build_analysis():
    sentiment, trades, merged = load_data()
    matched = merged[merged["classification"] != "Unmatched"].copy()

    by_sent = metric_frame(matched, ["classification"])
    by_sent["sort"] = by_sent["classification"].map(SENTIMENT_SCORE)
    by_sent = by_sent.sort_values("sort").drop(columns="sort")

    by_side = metric_frame(matched, ["classification", "side"])
    by_side["sort"] = by_side["classification"].map(SENTIMENT_SCORE)
    by_side = by_side.sort_values(["sort", "side"]).drop(columns="sort")

    by_direction = metric_frame(matched, ["classification", "direction"])
    by_direction["sort"] = by_direction["classification"].map(SENTIMENT_SCORE)
    by_direction = by_direction.sort_values(["sort", "direction"]).drop(columns="sort")

    daily = matched.groupby(["date", "classification"], dropna=False).agg(
        trades=("closed_pnl", "size"),
        accounts=("account", "nunique"),
        volume_usd=("size_usd", "sum"),
        total_pnl=("closed_pnl", "sum"),
        avg_pnl=("closed_pnl", "mean"),
        win_rate=("is_win", "mean"),
        avg_pnl_per_1k=("pnl_per_1k_usd", "mean"),
        total_fee=("fee", "sum"),
        sentiment_value=("value", "first"),
    ).reset_index().sort_values("date")

    account_sent = matched.groupby(["account", "classification"], dropna=False).agg(
        trades=("closed_pnl", "size"),
        volume_usd=("size_usd", "sum"),
        total_pnl=("closed_pnl", "sum"),
        win_rate=("is_win", "mean"),
        avg_pnl_per_1k=("pnl_per_1k_usd", "mean"),
    ).reset_index()
    active_accounts = account_sent.groupby("account")["trades"].sum()
    active_accounts = active_accounts[active_accounts >= 20].index
    account_sent = account_sent[account_sent["account"].isin(active_accounts)]
    account_pivot = account_sent.pivot_table(
        index="account",
        columns="classification",
        values="total_pnl",
        aggfunc="sum",
        fill_value=0,
    )
    account_pivot["total_trades"] = account_sent.groupby("account")["trades"].sum()
    account_pivot["total_pnl"] = account_sent.groupby("account")["total_pnl"].sum()
    account_pivot = account_pivot.sort_values("total_pnl", ascending=False).head(20).reset_index()

    top_symbols = metric_frame(matched, ["coin"])
    top_symbols = top_symbols.sort_values("volume_usd", ascending=False).head(20)

    corr = daily[["sentiment_value", "total_pnl", "avg_pnl", "win_rate", "volume_usd", "trades"]].corr(numeric_only=True)
    corr_rows = corr.reset_index().rename(columns={"index": "metric"})

    total_trades = len(merged)
    matched_trades = len(matched)
    unmatched = total_trades - matched_trades
    overall = {
        "total_trades": total_trades,
        "matched_trades": matched_trades,
        "unmatched_trades": unmatched,
        "match_rate": matched_trades / total_trades if total_trades else np.nan,
        "accounts": merged["account"].nunique(),
        "symbols": merged["coin"].nunique(),
        "date_min": merged["date"].min(),
        "date_max": merged["date"].max(),
        "sentiment_min": sentiment["date"].min(),
        "sentiment_max": sentiment["date"].max(),
        "total_volume": matched["size_usd"].sum(),
        "total_pnl": matched["closed_pnl"].sum(),
        "win_rate": matched["is_win"].mean(),
        "fees": matched["fee"].sum(),
    }

    best_sent = by_sent.sort_values("avg_pnl_per_1k", ascending=False).iloc[0]
    worst_sent = by_sent.sort_values("avg_pnl_per_1k", ascending=True).iloc[0]
    highest_pnl = by_sent.sort_values("total_pnl", ascending=False).iloc[0]
    highest_win = by_sent.sort_values("win_rate", ascending=False).iloc[0]
    corr_pnl = corr.loc["sentiment_value", "avg_pnl"] if "sentiment_value" in corr.index else np.nan
    corr_vol = corr.loc["sentiment_value", "volume_usd"] if "sentiment_value" in corr.index else np.nan
    insights = [
        f"Trades matched to sentiment on IST calendar date at {pct(overall['match_rate'])}; unmatched records are excluded from sentiment cuts.",
        f"Best risk-normalized regime: {best_sent['classification']} with {money(best_sent['avg_pnl_per_1k'])} average closed PnL per $1K traded.",
        f"Weakest risk-normalized regime: {worst_sent['classification']} with {money(worst_sent['avg_pnl_per_1k'])} average closed PnL per $1K traded.",
        f"Largest total PnL pool came from {highest_pnl['classification']} ({money(highest_pnl['total_pnl'])}), while the highest win rate was {highest_win['classification']} ({pct(highest_win['win_rate'])}).",
        f"Daily sentiment-value correlation with average trade PnL is {corr_pnl:.2f}; correlation with daily traded volume is {corr_vol:.2f}.",
        "Practical strategy read: compare trade sizing and direction by regime before increasing exposure; positive total PnL can hide poor PnL per dollar if volume is concentrated.",
    ]
    return {
        "sentiment": sentiment,
        "trades": trades,
        "merged": merged,
        "matched": matched,
        "by_sent": by_sent,
        "by_side": by_side,
        "by_direction": by_direction,
        "daily": daily,
        "account_pivot": account_pivot,
        "top_symbols": top_symbols,
        "corr": corr_rows,
        "overall": overall,
        "insights": insights,
    }


def clean_value(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if math.isnan(float(v)) else float(v)
    if pd.isna(v):
        return None
    return v


def write_df(ws, df: pd.DataFrame, start_row=1, start_col=1, title=None):
    row = start_row
    if title:
        ws.cell(row=row, column=start_col, value=title)
        ws.cell(row=row, column=start_col).font = Font(bold=True, size=13, color=COLORS["navy"])
        row += 1
    headers = list(df.columns)
    for j, h in enumerate(headers, start_col):
        cell = ws.cell(row=row, column=j, value=str(h).replace("_", " ").title())
        cell.font = Font(bold=True, color=COLORS["white"])
        cell.fill = PatternFill("solid", fgColor=COLORS["navy"])
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, rec in enumerate(df.to_dict("records"), row + 1):
        for j, h in enumerate(headers, start_col):
            ws.cell(row=i, column=j, value=clean_value(rec[h]))
    return row, row + len(df), start_col, start_col + len(headers) - 1


def style_sheet(ws):
    thin = Side(style="thin", color="D9E2F3")
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=thin)
            if isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0.00;[Red]-#,##0.00;'
    ws.freeze_panes = "A2"


def set_widths(ws, widths):
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def add_kpi(ws, cell, label, value, fill):
    ws[cell] = label
    ws[cell].font = Font(bold=True, color=COLORS["dark_gray"], size=10)
    ws[cell].fill = PatternFill("solid", fgColor=fill)
    ws[cell].alignment = Alignment(horizontal="center")
    value_cell = ws.cell(row=ws[cell].row + 1, column=ws[cell].column, value=value)
    value_cell.font = Font(bold=True, color=COLORS["navy"], size=16)
    value_cell.fill = PatternFill("solid", fgColor=fill)
    value_cell.alignment = Alignment(horizontal="center")


def build_workbook(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Executive Dashboard"

    ws["A1"] = "Hyperliquid Trader Performance vs Bitcoin Market Sentiment"
    ws["A1"].font = Font(bold=True, size=18, color=COLORS["navy"])
    ws["A2"] = "Analyst workbook: sentiment merge, regime performance, behavior patterns, and strategy implications"
    ws["A2"].font = Font(italic=True, color=COLORS["dark_gray"])

    o = data["overall"]
    add_kpi(ws, "A4", "Matched Trades", f"{o['matched_trades']:,}", COLORS["light_blue"])
    add_kpi(ws, "C4", "Match Rate", pct(o["match_rate"]), COLORS["light_teal"])
    add_kpi(ws, "E4", "Total Closed PnL", money(o["total_pnl"]), COLORS["light_green"] if o["total_pnl"] >= 0 else COLORS["light_red"])
    add_kpi(ws, "G4", "Win Rate", pct(o["win_rate"]), COLORS["light_amber"])
    add_kpi(ws, "I4", "Traded Volume", money(o["total_volume"]), COLORS["gray"])

    ws["A8"] = "Executive Findings"
    ws["A8"].font = Font(bold=True, size=14, color=COLORS["navy"])
    for idx, text in enumerate(data["insights"], 9):
        ws.cell(idx, 1, value=f"{idx-8}. {text}")
        ws.cell(idx, 1).alignment = Alignment(wrap_text=True, vertical="top")

    dash_sent = data["by_sent"][["classification", "trades", "volume_usd", "total_pnl", "avg_pnl", "win_rate", "avg_pnl_per_1k", "profit_factor"]].copy()
    write_df(ws, dash_sent, 17, 1, "Regime Scorecard")
    for row in range(19, 19 + len(dash_sent)):
        ws.cell(row, 5).number_format = '$#,##0;[Red]-$#,##0'
        ws.cell(row, 6).number_format = '$#,##0.00;[Red]-$#,##0.00'
        ws.cell(row, 7).number_format = '0.0%'
        ws.cell(row, 8).number_format = '$#,##0.00;[Red]-$#,##0.00'
    ws.conditional_formatting.add(f"D19:D{18+len(dash_sent)}", ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))
    ws.conditional_formatting.add(f"H19:H{18+len(dash_sent)}", ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))

    chart = BarChart()
    chart.title = "Total PnL by Sentiment Regime"
    chart.y_axis.title = "Closed PnL"
    chart.x_axis.title = "Regime"
    chart.add_data(Reference(ws, min_col=5, min_row=18, max_row=18 + len(dash_sent)), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=19, max_row=18 + len(dash_sent)))
    chart.height = 7
    chart.width = 13
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showVal = False
    ws.add_chart(chart, "J17")

    style_sheet(ws)
    set_widths(ws, {"A": 26, "B": 14, "C": 16, "D": 16, "E": 16, "F": 14, "G": 14, "H": 16, "I": 14, "J": 18, "K": 18, "L": 18, "M": 18})
    ws.merge_cells("A1:I1")
    ws.merge_cells("A2:I2")
    for r in range(9, 15):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)

    sheets = [
        ("Sentiment Summary", data["by_sent"]),
        ("Side and Direction", data["by_side"]),
        ("Direction Summary", data["by_direction"]),
        ("Daily Trend", data["daily"]),
        ("Top Accounts", data["account_pivot"]),
        ("Top Symbols", data["top_symbols"]),
        ("Correlation Matrix", data["corr"]),
    ]
    for name, df in sheets:
        wsx = wb.create_sheet(name)
        write_df(wsx, df, 1, 1)
        style_sheet(wsx)
        for col in range(1, min(wsx.max_column, 14) + 1):
            header = str(wsx.cell(1, col).value or "")
            width = max(12, min(30, len(header) + 4))
            wsx.column_dimensions[get_column_letter(col)].width = width
        for row in wsx.iter_rows(min_row=2):
            for cell in row:
                header = str(wsx.cell(1, cell.column).value or "").lower()
                if "pnl" in header or "fee" in header or "volume" in header or "size" in header:
                    cell.number_format = '$#,##0.00;[Red]-$#,##0.00'
                elif "rate" in header:
                    cell.number_format = '0.0%'
        if name == "Daily Trend" and len(df) > 1:
            line = LineChart()
            line.title = "Daily Sentiment Value and Average PnL"
            line.y_axis.title = "Value / Avg PnL"
            line.x_axis.title = "Date"
            line.add_data(Reference(wsx, min_col=5, min_row=1, max_row=min(len(df) + 1, 80)), titles_from_data=True)
            line.add_data(Reference(wsx, min_col=10, min_row=1, max_row=min(len(df) + 1, 80)), titles_from_data=True)
            line.set_categories(Reference(wsx, min_col=1, min_row=2, max_row=min(len(df) + 1, 80)))
            line.height = 7
            line.width = 15
            wsx.add_chart(line, "L2")

    src = wb.create_sheet("Sources & Assumptions")
    rows = [
        ["Input", str(FEAR_GREED)],
        ["Input", str(TRADES)],
        ["Sentiment date range", f"{o['sentiment_min']} to {o['sentiment_max']}"],
        ["Trade date range", f"{o['date_min']} to {o['date_max']}"],
        ["Merge rule", "Trader Timestamp IST converted to calendar date, joined to fear_greed_index date."],
        ["Performance field", "Closed PnL is treated as realized performance; win rate is Closed PnL > 0."],
        ["Normalization", "Avg PnL per $1K traded = Closed PnL / Size USD * 1,000."],
        ["Excluded from sentiment cuts", f"{o['unmatched_trades']:,} trades without matching sentiment date."],
        ["Analyst note", "Use regime-level PnL together with normalized PnL and profit factor; total PnL alone can be distorted by volume concentration."],
    ]
    write_df(src, pd.DataFrame(rows, columns=["Topic", "Detail"]), 1, 1)
    style_sheet(src)
    set_widths(src, {"A": 28, "B": 110})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_FILE)
    return OUT_FILE, data


if __name__ == "__main__":
    analysis = build_analysis()
    path, data = build_workbook(analysis)
    print(path)
    print(f"rows={len(data['merged'])} matched={len(data['matched'])} accounts={data['overall']['accounts']} symbols={data['overall']['symbols']}")
