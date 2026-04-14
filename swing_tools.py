import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from crewai.tools import tool
from tavily import TavilyClient
import os

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

        sector_map = {
            "IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS"],
            "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "INDUSINDBK.NS"],
            "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS"],
            "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS"],
            "FMCG": ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS"],
        }

        stocks_to_scan = sector_map.get(sector, NIFTY_500_STOCKS)

        for ticker in stocks_to_scan:
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

                # RSI oversold recovery (best swing signal)
                if 30 < latest_rsi < 50 and latest_rsi > prev_rsi:
                    swing_score += 3
                    signals.append(f"RSI recovering from oversold ({round(latest_rsi,1)})")

                # EMA20 above EMA50 (uptrend)
                if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]:
                    swing_score += 2
                    signals.append("EMA20 > EMA50 (uptrend)")

                # Price bouncing from lower Bollinger Band
                if current_price <= df["BB_lower"].iloc[-1] * 1.02:
                    swing_score += 2
                    signals.append("Bouncing from Bollinger lower band")

                # Volume spike confirms move
                if volume_spike and price_change > 0:
                    swing_score += 2
                    signals.append(f"Volume spike ({round(latest_volume/avg_volume,1)}x avg)")

                # Price above EMA20 (momentum)
                if current_price > df["EMA20"].iloc[-1]:
                    swing_score += 1
                    signals.append("Price above EMA20")

                if swing_score >= 4:
                    # Calculate entry, SL, target
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

            except Exception:
                continue

        # Sort by score
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:10]

        if not candidates:
            return "No strong swing candidates found today. Market may be trending down or sideways."

        result = "🔍 SWING TRADE CANDIDATES FOUND:\n\n"
        for c in candidates:
            result += f"""
📈 {c['ticker']}
- Price: ₹{c['price']} | RSI: {c['rsi']} | Score: {c['score']}/10
- Entry: ₹{c['entry']} | SL: ₹{c['stop_loss']} | Target: ₹{c['target']}
- Risk/Reward: {c['rr_ratio']}:1
- Signals: {', '.join(c['signals'])}
---"""

        return result

    except Exception as e:
        return f"Error scanning stocks: {str(e)}"


# ─── TOOL 2: GET STOCK DETAILS ────────────────────────────────────────────────
@tool("Get Detailed Stock Analysis")
def get_stock_details(ticker: str) -> str:
    """
    Gets detailed technical and fundamental analysis for a specific NSE stock.
    Input: NSE ticker with .NS suffix e.g. INFY.NS, TATAMOTORS.NS
    """
    try:
        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"

        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        info = stock.info

        if df.empty:
            return f"No data for {ticker}"

        # Technicals
        rsi = RSIIndicator(close=df["Close"], window=14).rsi()
        macd = MACD(close=df["Close"])
        ema20 = EMAIndicator(close=df["Close"], window=20).ema_indicator()
        ema50 = EMAIndicator(close=df["Close"], window=50).ema_indicator()
        atr = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14).average_true_range()

        current_price = round(df["Close"].iloc[-1], 2)
        week_high = round(df["High"].iloc[-5:].max(), 2)
        week_low = round(df["Low"].iloc[-5:].min(), 2)
        month_change = round(((current_price - df["Close"].iloc[-21]) / df["Close"].iloc[-21]) * 100, 2)
        week_change = round(((current_price - df["Close"].iloc[-5]) / df["Close"].iloc[-5]) * 100, 2)

        # Support/Resistance
        support = round(df["Low"].iloc[-20:].min(), 2)
        resistance = round(df["High"].iloc[-20:].max(), 2)

        # Fundamentals
        pe = info.get("trailingPE", "N/A")
        sector = info.get("sector", "N/A")
        market_cap = info.get("marketCap", 0)
        market_cap_cr = f"₹{round(market_cap/1e7):,} Cr" if market_cap else "N/A"

        return f"""
📊 DETAILED ANALYSIS: {ticker}

💰 PRICE DATA:
- Current: ₹{current_price}
- Week Change: {week_change}%
- Month Change: {month_change}%
- Week High/Low: ₹{week_high} / ₹{week_low}
- Support: ₹{support} | Resistance: ₹{resistance}

📈 TECHNICALS:
- RSI (14): {round(rsi.iloc[-1], 2)}
- MACD: {round(macd.macd().iloc[-1], 4)} | Signal: {round(macd.macd_signal().iloc[-1], 4)}
- EMA20: ₹{round(ema20.iloc[-1], 2)} | EMA50: ₹{round(ema50.iloc[-1], 2)}
- ATR (14): ₹{round(atr.iloc[-1], 2)}
- Trend: {'Bullish' if ema20.iloc[-1] > ema50.iloc[-1] else 'Bearish'}

🏢 FUNDAMENTALS:
- Sector: {sector}
- Market Cap: {market_cap_cr}
- PE Ratio: {round(pe, 2) if isinstance(pe, float) else pe}
"""

    except Exception as e:
        return f"Error: {str(e)}"


# ─── TOOL 3: MARKET MOOD ─────────────────────────────────────────────────────
@tool("Get Overall Market Mood")
def get_market_mood(dummy: str = "check") -> str:
    """
    Checks overall Indian market mood using Nifty 50, Bank Nifty, India VIX.
    Returns whether market conditions favor swing trading today.
    Input: any string like 'check'
    """
    try:
        indices = {
            "Nifty 50": "^NSEI",
            "Bank Nifty": "^NSEBANK",
            "India VIX": "^INDIAVIX",
        }

        result = "🌡️ MARKET MOOD CHECK:\n\n"
        overall_bullish = 0

        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d")
                if df.empty:
                    continue

                current = round(df["Close"].iloc[-1], 2)
                prev = round(df["Close"].iloc[-2], 2)
                change = round(((current - prev) / prev) * 100, 2)
                trend = "📈" if change > 0 else "📉"

                result += f"{trend} {name}: {current} ({change:+.2f}%)\n"

                if name != "India VIX" and change > 0:
                    overall_bullish += 1
                if name == "India VIX" and current < 15:
                    overall_bullish += 1

            except:
                continue

        # SGX Nifty as pre-market indicator
        result += "\n"

        if overall_bullish >= 2:
            result += "✅ MARKET MOOD: BULLISH — Good day for swing trade entries\n"
            result += "📊 Recommendation: Look for long setups\n"
        elif overall_bullish == 1:
            result += "⚠️ MARKET MOOD: NEUTRAL — Be selective with entries\n"
            result += "📊 Recommendation: Only highest conviction trades\n"
        else:
            result += "🔴 MARKET MOOD: BEARISH — Avoid new long entries today\n"
            result += "📊 Recommendation: Stay in cash, wait for better setup\n"

        return result

    except Exception as e:
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
        query = f"{company} India stock news March 2026"

        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query, max_results=5)

        positive_keywords = [
            "buy", "upgrade", "target", "growth", "profit", "beat", "strong",
            "order", "contract", "expansion", "dividend", "record", "surge"
        ]
        negative_keywords = [
            "sell", "downgrade", "loss", "miss", "weak", "cut", "concern",
            "fraud", "fine", "penalty", "decline", "drop", "warning"
        ]

        headlines = []
        positive_count = 0
        negative_count = 0

        for r in results["results"]:
            title = r["title"]
            headlines.append(f"  - {title}")
            if any(kw in title.lower() for kw in positive_keywords):
                positive_count += 1
            if any(kw in title.lower() for kw in negative_keywords):
                negative_count += 1

        if positive_count > negative_count:
            sentiment = "🟢 Positive — supports swing buy"
        elif negative_count > positive_count:
            sentiment = "🔴 Negative — avoid swing buy"
        else:
            sentiment = "🟡 Neutral — trade based on technicals only"

        return f"""
📰 NEWS: {ticker}
- Sentiment: {sentiment}
- Positive headlines: {positive_count}/5
- Negative headlines: {negative_count}/5
- Headlines:
{chr(10).join(headlines)}
"""
    except Exception as e:
        return f"Error fetching news: {str(e)}"


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
            return "❌ Telegram credentials missing in .env"

        # Telegram has 4096 char limit — split if needed
        max_length = 4000
        messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]

        for msg in messages:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = requests.post(url, data={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            })
            result = response.json()
            if not result.get("ok"):
                # Try without markdown if it fails
                response = requests.post(url, data={
                    "chat_id": chat_id,
                    "text": msg,
                })

        return "✅ Report sent to Telegram successfully!"

    except Exception as e:
        return f"❌ Telegram send failed: {str(e)}"
