# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from crewai.tools import tool
from tavily import TavilyClient
from datetime import datetime
import os
import logging

# ─── LOGGING SETUP ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("swing_agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ─── NIFTY 500 STOCK LIST (Representative sample) ────────────────────────────
NIFTY_500_STOCKS = [
    # IT
    "INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "LTIM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS",
    # Banking
    "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "SBIN.NS", "INDUSINDBK.NS", "BANDHANBNK.NS", "IDFCFIRSTB.NS",
    # NBFC
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS",
    # Auto
    "TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
    "EICHERMOT.NS", "MOTHERSON.NS", "BALKRISIND.NS", "MRF.NS",
    # Pharma
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "AUROPHARMA.NS", "LUPIN.NS", "BIOCON.NS", "ALKEM.NS",
    # FMCG
    "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
    "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "EMAMILTD.NS",
    # Energy
    "RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "GAIL.NS",
    # Metals
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "SAIL.NS", "COALINDIA.NS",
    # Real Estate
    "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS",
    # Telecom
    "BHARTIARTL.NS", "IDEA.NS",
    # Aviation
    "INDIGO.NS",
    # Paints
    "ASIANPAINT.NS", "BERGEPAINT.NS", "KANSAINER.NS",
    # Consumer
    "TITAN.NS", "TRENT.NS", "DMART.NS", "ABFRL.NS",
    # Infrastructure
    "LT.NS", "ADANIPORTS.NS", "ADANIENT.NS", "SIEMENS.NS",
    # Healthcare
    "APOLLOHOSP.NS", "FORTIS.NS", "MAXHEALTH.NS",
    # Chemicals
    "PIDILITIND.NS", "SRF.NS", "AAVAS.NS", "ATUL.NS",
]


# ─── TOOL 1: SCAN STOCKS FOR SWING SETUP ─────────────────────────────────────
@tool("Scan Stocks for Swing Trading Setup")
def scan_swing_candidates(sector: str = "all") -> str:
    """
    Scans Nifty 500 stocks for bullish swing trading setups.
    Looks for: RSI oversold recovery, EMA crossover, Bollinger Band bounce.
    Input: 'all' to scan everything or sector name like 'IT', 'Banking', 'Pharma'
    """
    try:
        candidates = []
        # FIX P2: Track skipped tickers to surface system errors vs genuine no-signal
        skipped = []

        sector_map = {
            "IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS"],
            "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "INDUSINDBK.NS"],
            "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS"],
            "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS"],
            "FMCG": ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS"],
        }

        stocks_to_scan = sector_map.get(sector, NIFTY_500_STOCKS)

        for ticker in stocks_to_scan:
            # FIX P2: Named exception — log actual error, track which ticker failed
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period="3mo")

                if df.empty or len(df) < 30:
                    continue

                # RSI
                rsi = RSIIndicator(close=df["Close"], window=14)
                df["RSI"] = rsi.rsi()
                latest_rsi = df["RSI"].iloc[-1]
                prev_rsi = df["RSI"].iloc[-2]

                # EMA
                ema20 = EMAIndicator(close=df["Close"], window=20)
                ema50 = EMAIndicator(close=df["Close"], window=50)
                df["EMA20"] = ema20.ema_indicator()
                df["EMA50"] = ema50.ema_indicator()

                # Bollinger Bands
                bb = BollingerBands(close=df["Close"], window=20)
                df["BB_lower"] = bb.bollinger_lband()
                df["BB_upper"] = bb.bollinger_hband()
                df["BB_mid"] = bb.bollinger_mavg()

                # Price data
                current_price = df["Close"].iloc[-1]
                prev_price = df["Close"].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100

                # Volume
                avg_volume = df["Volume"].iloc[-20:].mean()
                latest_volume = df["Volume"].iloc[-1]
                volume_spike = latest_volume > (avg_volume * 1.5)

                # Swing score
                swing_score = 0
                signals = []

                if 30 < latest_rsi < 50 and latest_rsi > prev_rsi:
                    swing_score += 3
                    signals.append(f"RSI recovering from oversold ({round(latest_rsi,1)})")

                if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]:
                    swing_score += 2
                    signals.append("EMA20 > EMA50 (uptrend)")

                if current_price <= df["BB_lower"].iloc[-1] * 1.02:
                    swing_score += 2
                    signals.append("Bouncing from Bollinger lower band")

                if volume_spike and price_change > 0:
                    swing_score += 2
                    signals.append(f"Volume spike ({round(latest_volume/avg_volume,1)}x avg)")

                if current_price > df["EMA20"].iloc[-1]:
                    swing_score += 1
                    signals.append("Price above EMA20")

                if swing_score >= 4:
                    atr = AverageTrueRange(
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        window=14
                    )
                    df["ATR"] = atr.average_true_range()
                    latest_atr = df["ATR"].iloc[-1]

                    entry = round(current_price, 2)
                    stop_loss = round(current_price - (1.5 * latest_atr), 2)
                    target = round(current_price + (2.5 * latest_atr), 2)
                    risk_reward = round((target - entry) / (entry - stop_loss), 2)

                    candidates.append({
                        "ticker": ticker,
                        "price": entry,
                        "score": swing_score,
                        "rsi": round(latest_rsi, 1),
                        "signals": signals,
                        "entry": entry,
                        "stop_loss": stop_loss,
                        "target": target,
                        "rr_ratio": risk_reward,
                        "atr": round(latest_atr, 2),
                    })

            except Exception as e:
                # FIX P2: Log with actual reason, not silent drop
                logger.warning(f"Skipping {ticker}: {e}")
                skipped.append(ticker)
                continue

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:10]

        # FIX P2: Include skipped summary in output
        skip_warning = ""
        if skipped:
            skip_warning = (
                f"\nWARNING: {len(skipped)} ticker(s) skipped due to data/API errors: "
                f"{', '.join(skipped[:5])}{'...' if len(skipped) > 5 else ''}\n"
            )
            logger.warning(f"Total skipped: {len(skipped)} tickers — {skipped}")

        if not candidates:
            return "No strong swing candidates found today. Market may be trending down or sideways." + skip_warning

        result = "SWING TRADE CANDIDATES FOUND:\n\n"
        for c in candidates:
            result += (
                f"\n{c['ticker']}\n"
                f"- Price: Rs.{c['price']} | RSI: {c['rsi']} | Score: {c['score']}/10\n"
                f"- Entry: Rs.{c['entry']} | SL: Rs.{c['stop_loss']} | Target: Rs.{c['target']}\n"
                f"- Risk/Reward: {c['rr_ratio']}:1\n"
                f"- Signals: {', '.join(c['signals'])}\n"
                "---"
            )

        return result + skip_warning

    except Exception as e:
        logger.error(f"Fatal error in scan_swing_candidates: {e}")
        return f"Error scanning stocks: {str(e)}"


# ─── TOOL 2: GET STOCK DETAILS ────────────────────────────────────────────────
@tool("Get Detailed Stock Analysis")
def get_stock_details(ticker: str) -> str:
    """
    Gets detailed technical and fundamental analysis for a specific NSE stock.
    Input: NSE ticker with .NS suffix e.g. INFY.NS, TATAMOTORS.NS
    """
    try:
        # FIX (my review): Strip first then append — prevents INFY.NS.NS double suffix
        ticker = ticker.replace(".NS", "").replace(".BO", "") + ".NS"

        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        info = stock.info

        if df.empty:
            return f"No data for {ticker}"

        rsi = RSIIndicator(close=df["Close"], window=14).rsi()
        macd = MACD(close=df["Close"])
        ema20 = EMAIndicator(close=df["Close"], window=20).ema_indicator()
        ema50 = EMAIndicator(close=df["Close"], window=50).ema_indicator()
        atr = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14).average_true_range()

        current_price = round(df["Close"].iloc[-1], 2)
        n = len(df)

        # FIX P2: Degrade gracefully for thin/newly listed stocks
        week_high = round(df["High"].iloc[-min(5, n):].max(), 2)
        week_low = round(df["Low"].iloc[-min(5, n):].min(), 2)
        month_change = (
            round(((current_price - df["Close"].iloc[-21]) / df["Close"].iloc[-21]) * 100, 2)
            if n >= 21 else "N/A (insufficient history)"
        )
        week_change = (
            round(((current_price - df["Close"].iloc[-5]) / df["Close"].iloc[-5]) * 100, 2)
            if n >= 5 else "N/A (insufficient history)"
        )

        support = round(df["Low"].iloc[-20:].min(), 2)
        resistance = round(df["High"].iloc[-20:].max(), 2)

        pe = info.get("trailingPE", "N/A")
        sector = info.get("sector", "N/A")
        market_cap = info.get("marketCap", 0)
        market_cap_cr = f"Rs.{round(market_cap/1e7):,} Cr" if market_cap else "N/A"

        return (
            f"\nDETAILED ANALYSIS: {ticker}\n\n"
            f"PRICE DATA:\n"
            f"- Current: Rs.{current_price}\n"
            f"- Week Change: {week_change}%\n"
            f"- Month Change: {month_change}%\n"
            f"- Week High/Low: Rs.{week_high} / Rs.{week_low}\n"
            f"- Support: Rs.{support} | Resistance: Rs.{resistance}\n\n"
            f"TECHNICALS:\n"
            f"- RSI (14): {round(rsi.iloc[-1], 2)}\n"
            f"- MACD: {round(macd.macd().iloc[-1], 4)} | Signal: {round(macd.macd_signal().iloc[-1], 4)}\n"
            f"- EMA20: Rs.{round(ema20.iloc[-1], 2)} | EMA50: Rs.{round(ema50.iloc[-1], 2)}\n"
            f"- ATR (14): Rs.{round(atr.iloc[-1], 2)}\n"
            f"- Trend: {'Bullish' if ema20.iloc[-1] > ema50.iloc[-1] else 'Bearish'}\n\n"
            f"FUNDAMENTALS:\n"
            f"- Sector: {sector}\n"
            f"- Market Cap: {market_cap_cr}\n"
            f"- PE Ratio: {round(pe, 2) if isinstance(pe, float) else pe}\n"
        )

    except Exception as e:
        logger.error(f"Error in get_stock_details for {ticker}: {e}")
        return f"Error fetching details for {ticker}: {str(e)}"


# ─── TOOL 3: MARKET MOOD ─────────────────────────────────────────────────────
@tool("Get Overall Market Mood")
def get_market_mood(market: str = "all") -> str:
    """
    Checks overall Indian market mood using Nifty 50, Bank Nifty, India VIX.
    Returns whether market conditions favor swing trading today.
    Input: any string like 'all' or 'check'
    """
    try:
        indices = {
            "Nifty 50": "^NSEI",
            "Bank Nifty": "^NSEBANK",
            "India VIX": "^INDIAVIX",
        }

        result = "MARKET MOOD CHECK:\n\n"
        overall_bullish = 0

        for name, symbol in indices.items():
            # FIX P2: Named exception instead of bare except
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d")
                if df.empty or len(df) < 2:
                    logger.warning(f"Insufficient data for index {name} ({symbol})")
                    continue

                current = round(df["Close"].iloc[-1], 2)
                prev = round(df["Close"].iloc[-2], 2)
                change = round(((current - prev) / prev) * 100, 2)
                arrow = "UP" if change > 0 else "DOWN"

                result += f"{arrow} {name}: {current} ({change:+.2f}%)\n"

                if name != "India VIX" and change > 0:
                    overall_bullish += 1
                if name == "India VIX" and current < 15:
                    overall_bullish += 1

            except Exception as e:
                logger.warning(f"Failed to fetch index {name}: {e}")
                continue

        result += "\n"

        if overall_bullish >= 2:
            result += "MARKET MOOD: BULLISH -- Good day for swing trade entries\n"
            result += "Recommendation: Look for long setups\n"
        elif overall_bullish == 1:
            result += "MARKET MOOD: NEUTRAL -- Be selective with entries\n"
            result += "Recommendation: Only highest conviction trades\n"
        else:
            result += "MARKET MOOD: BEARISH -- Avoid new long entries today\n"
            result += "Recommendation: Stay in cash, wait for better setup\n"

        return result

    except Exception as e:
        logger.error(f"Fatal error in get_market_mood: {e}")
        return f"Error checking market mood: {str(e)}"


# ─── TOOL 4: NEWS FOR STOCK ───────────────────────────────────────────────────
@tool("Get Swing Trade News")
def get_swing_news(ticker: str) -> str:
    """
    Searches for recent positive/negative news for a stock to confirm swing trade.
    Input: stock ticker like INFY.NS or company name like 'Infosys'
    """
    try:
        company = ticker.replace(".NS", "").replace(".BO", "")

        # FIX P1: Build query from live datetime at call time.
        # Also pass days=7 to Tavily so it only returns genuinely recent results.
        today = datetime.now()
        query = f"{company} India stock news {today.strftime('%d %B %Y')}"

        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query, max_results=5, days=7)

        positive_keywords = [
            "buy", "upgrade", "target", "growth", "profit", "beat", "strong",
            "order", "contract", "expansion", "dividend", "record", "surge"
        ]
        negative_keywords = [
            "sell", "downgrade", "loss", "miss", "weak", "cut", "concern",
            "fraud", "fine", "penalty", "decline", "drop", "warning"
        ]

        # FIX P3: Use .get() with empty-list fallback — don't assume key exists
        items = results.get("results", [])

        if not items:
            return f"No recent news found for {ticker}. Trade based on technicals only."

        headlines = []
        positive_count = 0
        negative_count = 0

        for r in items:
            title = r.get("title", "")
            if not title:
                continue
            headlines.append(f"  - {title}")
            if any(kw in title.lower() for kw in positive_keywords):
                positive_count += 1
            if any(kw in title.lower() for kw in negative_keywords):
                negative_count += 1

        # FIX P3: Report against actual count, not hardcoded /5
        total = len(headlines)

        if positive_count > negative_count:
            sentiment = "Positive -- supports swing buy"
        elif negative_count > positive_count:
            sentiment = "Negative -- avoid swing buy"
        else:
            sentiment = "Neutral -- trade based on technicals only"

        return (
            f"\nNEWS: {ticker}\n"
            f"- Sentiment: {sentiment}\n"
            f"- Positive headlines: {positive_count}/{total}\n"
            f"- Negative headlines: {negative_count}/{total}\n"
            f"- Headlines:\n"
            f"{chr(10).join(headlines)}\n"
        )

    except Exception as e:
        logger.error(f"Error in get_swing_news for {ticker}: {e}")
        return f"Error fetching news for {ticker}: {str(e)}"


# ─── TOOL 5: SEND TELEGRAM ───────────────────────────────────────────────────
@tool("Send Telegram Report")
def send_telegram_report(message: str) -> str:
    """
    Sends the final swing trading report to Telegram.
    Input: the complete formatted report as a string.
    """
    try:
        import requests
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not token or not chat_id:
            return "Telegram credentials missing in .env"

        max_length = 4000
        messages_to_send = [message[i:i+max_length] for i in range(0, len(message), max_length)]

        for msg in messages_to_send:
            url = f"https://api.telegram.org/bot{token}/sendMessage"

            # Attempt 1: with Markdown formatting
            response = requests.post(url, data={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            }, timeout=10)
            result = response.json()

            # FIX P1: If Markdown fails, retry as plain text AND check the fallback result too
            if not result.get("ok"):
                logger.warning(
                    f"Markdown send failed ({result.get('description', 'unknown')}) "
                    f"— retrying as plain text"
                )
                fallback_response = requests.post(url, data={
                    "chat_id": chat_id,
                    "text": msg,
                }, timeout=10)
                fallback_result = fallback_response.json()

                # FIX P1: Both attempts failed — return the actual Telegram error, not a false success
                if not fallback_result.get("ok"):
                    error_desc = fallback_result.get("description", "Unknown Telegram error")
                    logger.error(f"Telegram send failed on both attempts: {error_desc}")
                    return f"Telegram send failed: {error_desc}"

        return "Report sent to Telegram successfully!"

    except Exception as e:
        logger.error(f"Telegram exception: {e}")
        return f"Telegram send failed: {str(e)}"
