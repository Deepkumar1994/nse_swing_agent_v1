# Indian Swing Trading AI Agent v1.0

An AI-powered swing trading agent for Indian equity markets (NSE) that scans Nifty 500 stocks and sends actionable trade recommendations via Telegram.

> **Note:** This is v1.0. Version 2.0 with advanced features (sector rotation, earnings check, delivery volume, relative strength, trade history) is available in a separate repository.

---

## 🚀 Features

- **Market Mood Detection** — checks Nifty 50, Bank Nifty, India VIX
- **Stock Scanner** — scans Nifty 500 for bullish swing setups
- **Technical Analysis** — RSI, MACD, EMA, Bollinger Bands, ATR
- **News Sentiment** — scans latest headlines via Tavily search
- **Telegram Alerts** — sends formatted report to your phone nightly
- **Automated Scheduling** — runs via Windows Task Scheduler at 8 PM
- **Report Saving** — saves daily report to dated text file

---

## 📁 Project Structure

```
swing-trading-agent/
├── main.py              # Main agent — 3 AI agents + tasks + crew
├── swing_tools.py       # Tools — scanner, technicals, market mood, news
├── .env                 # API keys — NOT committed to Git
├── .env.example         # Template for API keys — safe to commit
├── .gitignore           # Files excluded from Git
├── requirements.txt     # Python dependencies
├── run_agent.bat        # Windows batch file for Task Scheduler
└── README.md            # This file
```

---

## ⚙️ Setup

### 1. Prerequisites
- Python 3.11
- Windows (for Task Scheduler automation)
- Telegram account

### 2. Clone the repository
```bash
git clone https://github.com/yourusername/swing-trading-agent.git
cd swing-trading-agent
```

### 3. Create virtual environment
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Set up API keys
```bash
copy .env.example .env
```
Edit `.env` and fill in your actual API keys.

### 6. Set up Telegram Bot
1. Open Telegram → search `@BotFather`
2. Send `/newbot` → follow instructions → save the token
3. Send any message to your new bot
4. Open in browser: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Copy the `id` number — that's your Chat ID

### 7. Run manually
```bash
python main.py
```

### 8. Schedule automatic runs (Windows Task Scheduler)
1. Edit `run_agent.bat` — update the path to your project folder
2. Open Task Scheduler → Create Basic Task
3. Set trigger: Daily at 8:00 PM
4. Set action: Start `run_agent.bat`
5. In Properties → check "Wake computer to run this task"

---

## 🔑 API Keys Required

| Service | Purpose | Cost | Link |
|---------|---------|------|------|
| Anthropic | Claude Haiku AI brain | ~$0.05/run | [console.anthropic.com](https://console.anthropic.com) |
| Tavily | News search | Free (1000/month) | [tavily.com](https://tavily.com) |
| Telegram Bot | Send alerts | Free | [@BotFather](https://t.me/botfather) |

---

## 🤖 How It Works

```
8:00 PM Daily(Run Manually according to your time)
     ↓
Agent 1: Market Analyst
  → Checks Nifty 50, Bank Nifty, India VIX
  → Scans Nifty 500 for swing setups using:
     - RSI recovering from oversold (30-50)
     - EMA20 > EMA50 (uptrend)
     - Price bouncing from Bollinger lower band
     - Volume spike (1.5x average)
  → Returns top 5 candidates
     ↓
Agent 2: Research Analyst
  → Gets detailed technicals for top 3 stocks
  → Checks recent news sentiment
  → Confirms or rejects each setup
     ↓
Agent 3: Report Generator
  → Formats complete trade report
  → Sends report to Telegram
  → Saves report to dated text file
     ↓
You receive Telegram message with:
  - Market snapshot
  - 2-3 trade setups (Entry, SL, Target)
  - Risk/Reward ratio
  - Confidence level
```

---

## 📊 Technical Indicators Used

| Indicator | Purpose |
|-----------|---------|
| RSI (14) | Identifies oversold stocks recovering |
| EMA 20 / 50 | Confirms uptrend direction |
| Bollinger Bands | Finds bounce setups from lower band |
| ATR (14) | Calculates dynamic stop loss and target |
| Volume | Confirms genuine buying interest |

---

## 📈 Sample Trade Report

```
🇮🇳 SWING TRADE ALERT — 29 Mar 2026
═══════════════════════════════

📊 MARKET SNAPSHOT
▪ Nifty: 22,819 (-2.09%)
▪ VIX: 26.8 — High Fear

🏆 TODAY'S SWING TRADES

🔹 TRADE 1: WIPRO.NS
▪ Entry: ₹191.60
▪ Stop Loss: ₹183.82 (4.1% risk)
▪ Target: ₹204.57 (6.8% gain)
▪ Hold: 2-5 days
▪ Risk/Reward: 1.67:1
▪ Why: RSI recovering from oversold, volume spike
▪ Confidence: Medium

💰 POSITION SIZING (₹10,000)
▪ Per trade: ₹3,000-5,000
▪ Max 2 trades at a time
▪ Never risk more than 2% per trade

⚠️ Research only. Not SEBI advice.
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Framework | CrewAI |
| LLM | Claude Haiku (Anthropic) |
| Stock Data | yfinance |
| Technical Indicators | ta library |
| News Search | Tavily |
| Notifications | Telegram Bot API |
| Language | Python 3.11 |

---

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**.

- Not SEBI-registered investment advice
- Past recommendations do not guarantee future results
- Swing trading carries significant financial risk
- Always use stop losses
- Never invest money you cannot afford to lose
- The authors are not responsible for any trading losses

---

## 📝 License

MIT License — free to use, modify and distribute.
