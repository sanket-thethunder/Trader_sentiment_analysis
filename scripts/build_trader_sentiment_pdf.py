from __future__ import annotations

import math
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from build_trader_sentiment_report import build_analysis


OUT_DIR = Path.cwd() / "outputs" / "trader_sentiment_analysis"
PDF_FILE = OUT_DIR / "institutional_trader_sentiment_research_deck.pdf"

PAGE_W, PAGE_H = landscape((13.333 * inch, 7.5 * inch))

NAVY = colors.HexColor("#111827")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D0D5DD")
PAPER = colors.HexColor("#F8FAFC")
WHITE = colors.white
TEAL = colors.HexColor("#00A88E")
BLUE = colors.HexColor("#2F6FED")
AMBER = colors.HexColor("#F59E0B")
RED = colors.HexColor("#D92D20")
GREEN = colors.HexColor("#16A34A")
VIOLET = colors.HexColor("#7C3AED")
SLATE = colors.HexColor("#344054")

SOURCES = [
    ("Alternative.me Crypto Fear & Greed Index", "https://alternative.me/crypto/fear-and-greed-index/"),
    ("CME Group, 24/7 crypto risk management paper", "https://www.cmegroup.com/articles/2026/aligning-cryptocurrency-derivatives-with-spot-markets-measuring-the-247-trading-opportunity.html"),
    ("QuickNode Hyperliquid trades dataset docs", "https://www.quicknode.com/docs/hyperliquid/datasets/trades"),
    ("Farzulla, Extremity Premium, arXiv 2026", "https://arxiv.org/abs/2602.07018"),
]


def fmt_money(x: float, decimals=1) -> str:
    if pd.isna(x):
        return "n/a"
    sign = "-" if x < 0 else ""
    x = abs(float(x))
    if x >= 1_000_000_000:
        return f"{sign}${x / 1_000_000_000:.{decimals}f}B"
    if x >= 1_000_000:
        return f"{sign}${x / 1_000_000:.{decimals}f}M"
    if x >= 1_000:
        return f"{sign}${x / 1_000:.{decimals}f}K"
    return f"{sign}${x:,.0f}"


def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x * 100:.1f}%"


def fmt_num(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{int(round(x)):,}"


def wrapped(c, text, x, y, width, font="Helvetica", size=10, leading=13, color=INK, max_lines=None):
    c.setFillColor(color)
    c.setFont(font, size)
    approx = max(12, int(width / (size * 0.52)))
    lines = []
    for para in str(text).split("\n"):
        lines.extend(textwrap.wrap(para, width=approx) or [""])
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def title(c, eyebrow, headline, sub=None, page_no=None):
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.rect(0, PAGE_H - 0.68 * inch, PAGE_W, 0.68 * inch, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, PAGE_H - 0.68 * inch, 0.15 * inch, 0.68 * inch, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(0.42 * inch, PAGE_H - 0.39 * inch, eyebrow.upper())
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(0.42 * inch, PAGE_H - 1.03 * inch, headline)
    if sub:
        wrapped(c, sub, 0.42 * inch, PAGE_H - 1.33 * inch, PAGE_W - 1.2 * inch, size=10.5, leading=13, color=MUTED)
    return


def footer(c, note="Prepared from supplied Hyperliquid fills and Bitcoin Fear & Greed sentiment data. Not investment advice."):
    return


def card(c, x, y, w, h, label, value, accent=TEAL, hint=None):
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.roundRect(x, y, w, h, 8, stroke=1, fill=1)
    c.setFillColor(accent)
    c.rect(x, y + h - 0.07 * inch, w, 0.07 * inch, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(MUTED)
    c.drawString(x + 0.18 * inch, y + h - 0.34 * inch, label.upper())
    c.setFont("Helvetica-Bold", 23)
    c.setFillColor(NAVY)
    c.drawString(x + 0.18 * inch, y + 0.24 * inch, value)
    if hint:
        wrapped(c, hint, x + 0.18 * inch, y + 0.08 * inch, w - 0.34 * inch, size=7.0, leading=8, color=MUTED, max_lines=1)


def metric_table(c, df, x, y, col_w, row_h=0.32 * inch, header_fill=NAVY, font_size=8.2):
    headers = list(df.columns)
    c.setFillColor(header_fill)
    c.rect(x, y - row_h, sum(col_w), row_h, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", font_size)
    cx = x
    for h, w in zip(headers, col_w):
        wrapped(c, h, cx + 5, y - 14, w - 8, font="Helvetica-Bold", size=font_size, leading=8, color=WHITE, max_lines=2)
        cx += w
    y -= row_h
    for ridx, row in df.iterrows():
        fill = colors.HexColor("#F9FAFB") if ridx % 2 == 0 else WHITE
        c.setFillColor(fill)
        c.rect(x, y - row_h, sum(col_w), row_h, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#EAECF0"))
        c.line(x, y - row_h, x + sum(col_w), y - row_h)
        cx = x
        for h, w in zip(headers, col_w):
            val = row[h]
            align_right = isinstance(val, (int, float, np.integer, np.floating)) and h != "Regime"
            c.setFillColor(INK)
            c.setFont("Helvetica", font_size)
            txt = str(val)
            if align_right:
                c.drawRightString(cx + w - 6, y - 0.21 * inch, txt)
            else:
                max_chars = max(8, int((w - 12) / (font_size * 0.48)))
                max_lines = max(1, int((row_h - 8) / (font_size + 2)))
                lines = textwrap.wrap(txt, width=max_chars)[:max_lines]
                ty = y - 0.16 * inch
                for line in lines:
                    c.drawString(cx + 6, ty, line)
                    ty -= font_size + 2
            cx += w
        y -= row_h


def chart_title(c, x, y, text):
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, text)


def draw_bar_chart(c, x, y, w, h, labels, values, heading, color=TEAL, horizontal=False, money_axis=True):
    chart_title(c, x, y + h + 0.18 * inch, heading)
    vals = np.array([0 if pd.isna(v) else float(v) for v in values], dtype=float)
    labels = [str(l) for l in labels]
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=1)
    pad = 0.35 * inch
    if horizontal:
        maxv = max(abs(vals).max(), 1)
        bar_gap = h / max(len(vals), 1)
        zero_x = x + pad + (w - 1.65 * inch) * 0.28
        scale = (w - 1.95 * inch) * 0.68 / maxv
        for i, (lab, val) in enumerate(zip(labels, vals)):
            by = y + h - (i + 0.75) * bar_gap
            c.setFont("Helvetica", 7.5)
            c.setFillColor(MUTED)
            c.drawRightString(zero_x - 0.08 * inch, by + 2, lab)
            bw = abs(val) * scale
            bx = zero_x if val >= 0 else zero_x - bw
            c.setFillColor(color if val >= 0 else RED)
            c.rect(bx, by - 5, bw, 10, stroke=0, fill=1)
            c.setFillColor(INK)
            c.drawString((bx + bw + 4) if val >= 0 else (bx - 42), by - 2, fmt_money(val, 0) if money_axis else f"{val:,.0f}")
        c.setStrokeColor(LINE)
        c.line(zero_x, y + 0.2 * inch, zero_x, y + h - 0.2 * inch)
    else:
        minv = min(vals.min(), 0)
        maxv = max(vals.max(), 1)
        span = maxv - minv if maxv != minv else 1
        plot_x = x + 0.55 * inch
        plot_y = y + 0.52 * inch
        plot_w = w - 0.85 * inch
        plot_h = h - 0.9 * inch
        zero_y = plot_y + (0 - minv) / span * plot_h
        c.setStrokeColor(LINE)
        c.line(plot_x, zero_y, plot_x + plot_w, zero_y)
        gap = plot_w / max(len(vals), 1)
        for i, (lab, val) in enumerate(zip(labels, vals)):
            bx = plot_x + i * gap + gap * 0.18
            bw = gap * 0.58
            bh = abs(val) / span * plot_h
            by = zero_y if val >= 0 else zero_y - bh
            c.setFillColor(color if val >= 0 else RED)
            c.rect(bx, by, bw, bh, stroke=0, fill=1)
            c.setFont("Helvetica", 7)
            c.setFillColor(MUTED)
            c.saveState()
            c.translate(bx + bw / 2 - 3, y + 0.16 * inch)
            c.rotate(25)
            c.drawString(0, 0, lab[:16])
            c.restoreState()
            c.setFillColor(INK)
            c.drawCentredString(bx + bw / 2, by + bh + 4 if val >= 0 else by - 11, fmt_money(val, 0) if money_axis else f"{val:,.0f}")


def draw_line_chart(c, x, y, w, h, df):
    chart_title(c, x, y + h + 0.18 * inch, "Daily sentiment value vs average realized PnL")
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=1)
    sample = df.sort_values("date").copy()
    if len(sample) > 120:
        sample = sample.iloc[np.linspace(0, len(sample) - 1, 120).astype(int)]
    sx = x + 0.45 * inch
    sy = y + 0.42 * inch
    sw = w - 0.75 * inch
    sh = h - 0.8 * inch
    c.setStrokeColor(LINE)
    for k in range(4):
        yy = sy + k * sh / 3
        c.line(sx, yy, sx + sw, yy)
    def points(series):
        vals = pd.Series(series).astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).values
        vmin, vmax = vals.min(), vals.max()
        if vmax == vmin:
            vmax += 1
        return [(sx + i * sw / max(len(vals) - 1, 1), sy + (v - vmin) / (vmax - vmin) * sh) for i, v in enumerate(vals)]
    for pts, col in [(points(sample["sentiment_value"]), BLUE), (points(sample["avg_pnl"]), TEAL)]:
        c.setStrokeColor(col)
        c.setLineWidth(1.4)
        for p1, p2 in zip(pts, pts[1:]):
            c.line(p1[0], p1[1], p2[0], p2[1])
    c.setLineWidth(1)
    c.setFillColor(BLUE); c.rect(x + w - 2.05 * inch, y + h - 0.33 * inch, 0.1 * inch, 0.1 * inch, stroke=0, fill=1)
    c.setFillColor(MUTED); c.setFont("Helvetica", 8); c.drawString(x + w - 1.9 * inch, y + h - 0.33 * inch, "Sentiment value")
    c.setFillColor(TEAL); c.rect(x + w - 2.05 * inch, y + h - 0.55 * inch, 0.1 * inch, 0.1 * inch, stroke=0, fill=1)
    c.setFillColor(MUTED); c.drawString(x + w - 1.9 * inch, y + h - 0.55 * inch, "Avg PnL")


def draw_heatmap(c, x, y, w, h, matrix, heading):
    chart_title(c, x, y + h + 0.18 * inch, heading)
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=1)
    vals = matrix.values.astype(float)
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    if vmax == vmin:
        vmax += 1
    left = x + 1.25 * inch
    top = y + h - 0.45 * inch
    cell_w = (w - 1.55 * inch) / max(matrix.shape[1], 1)
    cell_h = (h - 0.9 * inch) / max(matrix.shape[0], 1)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(MUTED)
    for j, col in enumerate(matrix.columns):
        c.drawCentredString(left + j * cell_w + cell_w / 2, top + 0.13 * inch, str(col))
    for i, idx in enumerate(matrix.index):
        yy = top - (i + 1) * cell_h
        c.setFillColor(MUTED)
        c.drawRightString(left - 0.08 * inch, yy + cell_h / 2 - 3, str(idx))
        for j in range(matrix.shape[1]):
            val = float(matrix.iloc[i, j])
            norm = (val - vmin) / (vmax - vmin)
            if val >= 0:
                fill = colors.Color(0.9 - 0.65 * norm, 0.98, 0.86 - 0.45 * norm)
            else:
                fill = colors.Color(1, 0.92 - 0.55 * (1 - norm), 0.90 - 0.55 * (1 - norm))
            c.setFillColor(fill)
            c.rect(left + j * cell_w, yy, cell_w - 2, cell_h - 2, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica", 7.5)
            c.drawCentredString(left + j * cell_w + cell_w / 2, yy + cell_h / 2 - 3, fmt_money(val, 0))


def enrich(data):
    matched = data["matched"].copy()
    by_sent = data["by_sent"].copy()
    side = data["by_side"].copy()
    daily = data["daily"].copy()
    account = data["account_pivot"].copy()

    by_sent["regime_order"] = by_sent["classification"].map({
        "Extreme Fear": 1, "Fear": 2, "Neutral": 3, "Greed": 4, "Extreme Greed": 5
    })
    by_sent = by_sent.sort_values("regime_order")
    by_sent["share_volume"] = by_sent["volume_usd"] / by_sent["volume_usd"].sum()
    by_sent["share_pnl"] = by_sent["total_pnl"] / by_sent["total_pnl"].sum()
    by_sent["fee_drag"] = by_sent["total_fee"] / by_sent["volume_usd"]

    side_matrix = side.pivot_table(index="classification", columns="side", values="total_pnl", fill_value=0)
    side_matrix = side_matrix.reindex(["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]).dropna(how="all")

    direction = data["by_direction"].copy()
    direction = direction[direction["trades"] >= 100].sort_values("avg_pnl_per_1k", ascending=False).head(12)

    top_accounts = account.copy()
    top_accounts["pnl_per_trade"] = top_accounts["total_pnl"] / top_accounts["total_trades"]
    top_accounts = top_accounts.sort_values("total_pnl", ascending=False).head(10)

    coin = data["top_symbols"].copy().sort_values("total_pnl", ascending=False).head(10)

    high_volume_days = daily.sort_values("volume_usd", ascending=False).head(5)
    best_days = daily.sort_values("total_pnl", ascending=False).head(5)
    worst_days = daily.sort_values("total_pnl", ascending=True).head(5)

    return {
        **data,
        "by_sent": by_sent,
        "side_matrix": side_matrix,
        "direction_top": direction,
        "top_accounts": top_accounts,
        "top_coin": coin,
        "high_volume_days": high_volume_days,
        "best_days": best_days,
        "worst_days": worst_days,
    }


def draw_cover(c, data):
    o = data["overall"]
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, 0, 0.18 * inch, PAGE_H, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#1F2937"))
    c.circle(PAGE_W - 1.7 * inch, PAGE_H - 1.4 * inch, 2.25 * inch, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(0.75 * inch, PAGE_H - 1.55 * inch, "Trader Performance vs")
    c.drawString(0.75 * inch, PAGE_H - 2.05 * inch, "Bitcoin Market Sentiment")
    wrapped(
        c,
        "Institutional-style research deck on Hyperliquid fills, realized PnL, sizing behavior, and Fear/Greed regimes.",
        0.78 * inch,
        PAGE_H - 2.55 * inch,
        6.5 * inch,
        size=13,
        leading=17,
        color=colors.HexColor("#D1D5DB"),
    )
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#9CA3AF"))
    c.drawString(0.78 * inch, 1.15 * inch, "RESEARCH DATE")
    c.drawString(2.45 * inch, 1.15 * inch, "DATA WINDOW")
    c.drawString(5.25 * inch, 1.15 * inch, "SAMPLE")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(WHITE)
    c.drawString(0.78 * inch, 0.76 * inch, "8 Jun 2026")
    c.drawString(2.45 * inch, 0.76 * inch, f"{o['date_min']} to {o['date_max']}")
    c.drawString(5.25 * inch, 0.76 * inch, f"{o['matched_trades']:,} matched fills")


def build_pdf(data):
    c = canvas.Canvas(str(PDF_FILE), pagesize=(PAGE_W, PAGE_H))
    draw_cover(c, data)
    c.showPage()

    o = data["overall"]
    page = 2

    title(c, "Executive thesis", "Sentiment is not the alpha; regime discipline is", "The dataset shows profitable trading across all regimes, but quality of PnL changes materially when viewed through sizing, win-rate, and PnL-per-dollar lenses.", page)
    footer(c)
    card(c, 0.65 * inch, 4.58 * inch, 3.1 * inch, 0.96 * inch, "Matched fills", f"{o['matched_trades']:,}", TEAL)
    card(c, 4.05 * inch, 4.58 * inch, 3.1 * inch, 0.96 * inch, "Total closed PnL", fmt_money(o["total_pnl"]), GREEN)
    card(c, 7.45 * inch, 4.58 * inch, 3.1 * inch, 0.96 * inch, "Win rate", fmt_pct(o["win_rate"]), BLUE)
    card(c, 0.65 * inch, 3.38 * inch, 3.1 * inch, 0.96 * inch, "Volume", fmt_money(o["total_volume"]), AMBER)
    card(c, 4.05 * inch, 3.38 * inch, 3.1 * inch, 0.96 * inch, "Accounts", fmt_num(o["accounts"]), VIOLET)
    bullets = [
        "Extreme Greed produced the strongest risk-normalized outcome; Extreme Fear had the weakest PnL per dollar even though it was still positive.",
        "Fear generated the largest absolute PnL pool, meaning total PnL is partly a volume allocation story, not only a signal-quality story.",
        "Daily sentiment-value correlation with average PnL is close to flat; the practical edge is conditional trade selection and sizing, not blind sentiment following.",
        "The trading-company playbook is to convert sentiment into risk budget rules: scale, side bias, and account review thresholds by regime.",
    ]
    y = 2.78 * inch
    for b in bullets:
        c.setFillColor(TEAL)
        c.circle(0.72 * inch, y + 0.04 * inch, 0.035 * inch, stroke=0, fill=1)
        y = wrapped(c, b, 0.9 * inch, y, 11.35 * inch, size=12, leading=17, color=INK) - 0.08 * inch
    c.showPage()
    page += 1

    title(c, "Research method", "A clean fill-level join, then regime-level trader diagnostics", "The analysis treats sentiment as a daily market state and evaluates realized trader behavior inside that state.", page)
    footer(c, "References: Alternative.me index methodology; QuickNode Hyperliquid trade-field definitions; CME crypto risk-management framing.")
    x = 0.65 * inch
    steps = [
        ("1", "Normalize data", "Parse IST timestamps, map to calendar date, clean numeric fields, and preserve fill-level records."),
        ("2", "Join market state", "Attach Fear/Greed classification and numeric sentiment value to every matched fill date."),
        ("3", "Measure performance", "Evaluate total PnL, average PnL, win rate, fee drag, profit factor, and PnL per $1K traded."),
        ("4", "Diagnose behavior", "Cut results by side, direction, account, symbol, and daily trend to separate alpha from exposure."),
    ]
    for i, (num, head, body) in enumerate(steps):
        sx = x + i * 3.18 * inch
        c.setFillColor(PAPER)
        c.roundRect(sx, 2.2 * inch, 2.75 * inch, 2.55 * inch, 8, stroke=0, fill=1)
        c.setFillColor(TEAL if i < 2 else BLUE)
        c.circle(sx + 0.35 * inch, 4.25 * inch, 0.22 * inch, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(sx + 0.35 * inch, 4.16 * inch, num)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(sx + 0.26 * inch, 3.65 * inch, head)
        wrapped(c, body, sx + 0.26 * inch, 3.25 * inch, 2.25 * inch, size=9.5, leading=13, color=MUTED)
    c.setFillColor(colors.HexColor("#EFF8FF"))
    c.roundRect(0.78 * inch, 1.12 * inch, 11.8 * inch, 0.56 * inch, 6, stroke=0, fill=1)
    wrapped(c, f"Data integrity note: {o['matched_trades']:,} of {o['total_trades']:,} fills matched to a sentiment date; {o['unmatched_trades']:,} unmatched fills were excluded from sentiment cuts.", 1.0 * inch, 1.36 * inch, 11.25 * inch, size=10, leading=12, color=INK)
    c.showPage()
    page += 1

    title(c, "Regime scorecard", "Absolute PnL and capital efficiency do not tell the same story", "A trading desk should read total PnL beside PnL per $1K, win rate, and profit factor before changing risk limits.", page)
    footer(c)
    draw_bar_chart(c, 0.58 * inch, 1.05 * inch, 6.0 * inch, 2.85 * inch, data["by_sent"]["classification"], data["by_sent"]["total_pnl"], "Total realized PnL by sentiment regime", TEAL)
    draw_bar_chart(c, 6.95 * inch, 1.05 * inch, 5.8 * inch, 2.85 * inch, data["by_sent"]["classification"], data["by_sent"]["avg_pnl_per_1k"], "PnL efficiency: avg PnL per $1K traded", BLUE)
    score = data["by_sent"][["classification", "trades", "total_pnl", "win_rate", "avg_pnl_per_1k", "profit_factor"]].copy()
    score.columns = ["Regime", "Fills", "Total PnL", "Win Rate", "PnL / $1K", "Profit Factor"]
    score["Fills"] = score["Fills"].map(lambda v: f"{int(v):,}")
    score["Total PnL"] = score["Total PnL"].map(fmt_money)
    score["Win Rate"] = score["Win Rate"].map(fmt_pct)
    score["PnL / $1K"] = score["PnL / $1K"].map(lambda v: fmt_money(v, 0))
    score["Profit Factor"] = score["Profit Factor"].map(lambda v: "n/a" if pd.isna(v) else f"{v:.2f}x")
    metric_table(c, score, 0.6 * inch, 5.0 * inch, [1.55 * inch, 1.0 * inch, 1.25 * inch, 1.0 * inch, 1.15 * inch, 1.15 * inch], row_h=0.31 * inch)
    c.showPage()
    page += 1

    title(c, "Trading behavior", "Side-level performance shows where regime exposure really sits", "The strongest desk use-case is not asking whether Fear or Greed is good; it is asking which behavior is rewarded under each state.", page)
    footer(c)
    draw_heatmap(c, 0.55 * inch, 1.0 * inch, 7.25 * inch, 3.9 * inch, data["side_matrix"], "Side-level PnL by sentiment regime")
    right_x = 8.05 * inch
    c.setFillColor(PAPER)
    c.roundRect(right_x, 1.2 * inch, 4.55 * inch, 4.05 * inch, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(right_x + 0.28 * inch, 4.75 * inch, "Desk interpretation")
    notes = [
        "Side and direction cuts expose whether PnL is coming from deliberate regime adaptation or simply from more trading activity.",
        "If a side dominates PnL in a regime, the next test should be drawdown, slippage, and fee-adjusted return by that side.",
        "Use this as a risk-routing layer: trade authorization, position size, and review cadence should differ by sentiment state.",
    ]
    y = 4.22 * inch
    for n in notes:
        y = wrapped(c, n, right_x + 0.35 * inch, y, 3.95 * inch, size=10.5, leading=15, color=INK) - 0.18 * inch
    c.showPage()
    page += 1

    title(c, "Daily dynamics", "Sentiment co-moves with activity more than it directly explains PnL", "The daily view keeps the analysis honest: regime labels are useful context, but PnL remains trader- and execution-dependent.", page)
    footer(c)
    draw_line_chart(c, 0.55 * inch, 1.2 * inch, 7.7 * inch, 4.1 * inch, data["daily"])
    corr = data["daily"][["sentiment_value", "total_pnl", "avg_pnl", "win_rate", "volume_usd", "trades"]].corr(numeric_only=True)
    rows = pd.DataFrame([
        ["Avg PnL", f"{corr.loc['sentiment_value', 'avg_pnl']:.2f}"],
        ["Total PnL", f"{corr.loc['sentiment_value', 'total_pnl']:.2f}"],
        ["Win rate", f"{corr.loc['sentiment_value', 'win_rate']:.2f}"],
        ["Volume", f"{corr.loc['sentiment_value', 'volume_usd']:.2f}"],
        ["Fill count", f"{corr.loc['sentiment_value', 'trades']:.2f}"],
    ], columns=["Daily metric", "Corr. vs sentiment"])
    metric_table(c, rows, 8.55 * inch, 4.95 * inch, [1.7 * inch, 1.45 * inch], row_h=0.31 * inch, font_size=8.3)
    wrapped(c, "Read: a low raw correlation does not invalidate sentiment. It means sentiment is better used as a conditional risk-management variable than as a standalone directional predictor.", 8.55 * inch, 2.35 * inch, 3.6 * inch, size=10.2, leading=14, color=INK)
    c.showPage()
    page += 1

    title(c, "Account concentration", "A small set of accounts explains much of the realized edge", "Trading-company review should separate regime quality from trader skill concentration.", page)
    footer(c)
    draw_bar_chart(c, 0.55 * inch, 1.1 * inch, 6.3 * inch, 4.0 * inch, data["top_accounts"]["account"].str[:10] + "...", data["top_accounts"]["total_pnl"], "Top account contribution to realized PnL", VIOLET, horizontal=True)
    top = data["top_accounts"][["account", "total_trades", "total_pnl", "pnl_per_trade"]].copy()
    top["account"] = top["account"].str[:12] + "..."
    top.columns = ["Account", "Fills", "Total PnL", "PnL / Fill"]
    top["Fills"] = top["Fills"].map(lambda v: f"{int(v):,}")
    top["Total PnL"] = top["Total PnL"].map(fmt_money)
    top["PnL / Fill"] = top["PnL / Fill"].map(lambda v: fmt_money(v, 0))
    metric_table(c, top.head(8), 7.18 * inch, 5.25 * inch, [1.55 * inch, 0.8 * inch, 1.05 * inch, 1.05 * inch], row_h=0.34 * inch, font_size=8.5)
    wrapped(c, "Action: benchmark top accounts by regime-specific process, not just outcome. The repeatable learning is how they size and close positions when sentiment is crowded.", 7.25 * inch, 1.75 * inch, 4.5 * inch, size=10.5, leading=15, color=INK)
    c.showPage()
    page += 1

    title(c, "Symbol contribution", "Profits cluster by market; symbol mix can mask sentiment conclusions", "A regime may look strong because the traded symbols in that regime were favorable, not because sentiment alone created edge.", page)
    footer(c)
    draw_bar_chart(c, 0.55 * inch, 1.15 * inch, 6.5 * inch, 4.0 * inch, data["top_coin"]["coin"], data["top_coin"]["total_pnl"], "Top symbols by realized PnL", AMBER, horizontal=True)
    coin = data["top_coin"][["coin", "trades", "volume_usd", "total_pnl", "avg_pnl_per_1k"]].copy()
    coin.columns = ["Symbol", "Fills", "Volume", "Total PnL", "PnL / $1K"]
    coin["Fills"] = coin["Fills"].map(lambda v: f"{int(v):,}")
    coin["Volume"] = coin["Volume"].map(fmt_money)
    coin["Total PnL"] = coin["Total PnL"].map(fmt_money)
    coin["PnL / $1K"] = coin["PnL / $1K"].map(lambda v: fmt_money(v, 0))
    metric_table(c, coin.head(8), 7.25 * inch, 5.18 * inch, [0.75 * inch, 0.75 * inch, 1.05 * inch, 1.05 * inch, 1.05 * inch], row_h=0.34 * inch, font_size=8.2)
    c.showPage()
    page += 1

    title(c, "Stress days", "High-volume and loss days should become risk-rule exceptions", "The institutional move is to translate outlier days into pre-trade controls and post-trade review triggers.", page)
    footer(c)
    best = data["best_days"][["date", "classification", "total_pnl", "volume_usd", "win_rate"]].copy()
    worst = data["worst_days"][["date", "classification", "total_pnl", "volume_usd", "win_rate"]].copy()
    high = data["high_volume_days"][["date", "classification", "volume_usd", "total_pnl", "win_rate"]].copy()
    for df in [best, worst, high]:
        for col in ["total_pnl", "volume_usd"]:
            if col in df:
                df[col] = df[col].map(fmt_money)
        df["win_rate"] = df["win_rate"].map(fmt_pct)
        df.columns = [str(c).replace("_", " ").title() for c in df.columns]
    metric_table(c, best, 0.65 * inch, 5.0 * inch, [1.05 * inch, 1.25 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch], row_h=0.32 * inch, font_size=8)
    c.setFillColor(GREEN); c.setFont("Helvetica-Bold", 12); c.drawString(0.65 * inch, 5.25 * inch, "Best PnL days")
    metric_table(c, worst, 6.9 * inch, 5.0 * inch, [1.05 * inch, 1.25 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch], row_h=0.32 * inch, font_size=8)
    c.setFillColor(RED); c.setFont("Helvetica-Bold", 12); c.drawString(6.9 * inch, 5.25 * inch, "Worst PnL days")
    metric_table(c, high, 3.35 * inch, 2.25 * inch, [1.05 * inch, 1.25 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch], row_h=0.32 * inch, font_size=8)
    c.setFillColor(AMBER); c.setFont("Helvetica-Bold", 12); c.drawString(3.35 * inch, 2.5 * inch, "Highest-volume days")
    c.showPage()
    page += 1

    title(c, "Strategy playbook", "Convert sentiment into a risk budget, not a buy/sell button", "A practical trading-company framework uses sentiment to change position sizing, review intensity, and execution standards.", page)
    footer(c)
    playbook = pd.DataFrame([
        ["Extreme Fear", "Defense first", "Reduce impulse entries; require liquidity check; favor smaller clips", "High uncertainty / adverse-selection risk"],
        ["Fear", "Selective offense", "Allow risk where account/symbol edge is proven; monitor fee drag", "Largest PnL pool but volume-driven"],
        ["Neutral", "Baseline", "Use standard limits; no sentiment-based override", "Control state"],
        ["Greed", "Momentum with guardrails", "Permit trend exposure; tighten loss review and take-profit discipline", "Crowding risk rising"],
        ["Extreme Greed", "High-quality offense", "Scale only for accounts with proven efficiency; avoid late crowded trades", "Best PnL per $1K in this dataset"],
    ], columns=["Regime", "Desk posture", "Trading rule", "Why"])
    metric_table(c, playbook, 0.55 * inch, 5.2 * inch, [1.15 * inch, 1.35 * inch, 5.25 * inch, 3.9 * inch], row_h=0.72 * inch, font_size=8.0)
    c.setFillColor(colors.HexColor("#ECFDF3"))
    c.roundRect(0.78 * inch, 0.72 * inch, 11.75 * inch, 0.62 * inch, 8, stroke=0, fill=1)
    wrapped(c, "Recommended next test: backtest these regime-specific rules using fee-adjusted PnL, adverse excursion, and drawdown by account.", 1.0 * inch, 1.08 * inch, 11.25 * inch, size=10.0, leading=12, color=INK)
    c.showPage()
    page += 1

    title(c, "Reference framing", "External context used to shape the trading-company narrative", "These references were used for methodology framing and industry-style interpretation; the empirical results come from the supplied CSV files.", page)
    footer(c)
    ref_notes = [
        ("Sentiment index construction", "Alternative.me frames the Crypto Fear & Greed Index as a Bitcoin-market sentiment gauge built from inputs such as volatility, market momentum/volume, social media, dominance, and trends."),
        ("24/7 risk-management lens", "CME's 2026 crypto paper emphasizes continuous price discovery and risk management because crypto volatility persists outside traditional market hours."),
        ("Fill-level data interpretation", "QuickNode's Hyperliquid trade dataset documentation defines executed fills and fields including side, direction, closedPnl, fees, trade IDs, and timestamps."),
        ("Regime extremity caution", "Recent quantitative research on Fear & Greed regimes argues that sentiment extremes can proxy uncertainty and liquidity stress, so extremes need risk controls."),
    ]
    y = 5.15 * inch
    for head, body in ref_notes:
        c.setFillColor(PAPER)
        c.roundRect(0.75 * inch, y - 0.62 * inch, 11.7 * inch, 0.56 * inch, 6, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1.0 * inch, y - 0.23 * inch, head)
        wrapped(c, body, 3.25 * inch, y - 0.2 * inch, 8.8 * inch, size=9.2, leading=11, color=INK, max_lines=2)
        y -= 0.78 * inch
    c.showPage()

    c.save()
    return PDF_FILE


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = build_analysis()
    data = enrich(raw)
    path = build_pdf(data)
    print(path)
