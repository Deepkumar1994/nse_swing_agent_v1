from crewai import Agent, Task, Crew, LLM, Process
from dotenv import load_dotenv
from swing_tools import (
    scan_swing_candidates,
    get_stock_details,
    get_market_mood,
    get_swing_news,
    send_telegram_report,
)
from datetime import datetime
import os

load_dotenv()

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = LLM(model="claude-haiku-4-5")

# ─── AGENTS ──────────────────────────────────────────────────────────────────

market_agent = Agent(
    role="Indian Market Analyst",
    goal="Check overall market mood and scan for best swing trade candidates.",
    backstory="Expert in Indian equity markets, scans Nifty 500 for momentum setups.",
    tools=[get_market_mood, scan_swing_candidates],
    llm=llm,
    verbose=True,
    max_iter=5,
)

research_agent = Agent(
    role="Stock Research Analyst",
    goal="Deep dive into top candidates — technicals, fundamentals and news.",
    backstory="Experienced analyst who validates swing trade setups with multiple data points.",
    tools=[get_stock_details, get_swing_news],
    llm=llm,
    verbose=True,
    max_iter=6,
)

reporter_agent = Agent(
    role="Trading Report Generator",
    goal="Generate actionable swing trade report and send it to Telegram.",
    backstory="Professional trader who creates clear, actionable trade plans.",
    tools=[send_telegram_report],
    llm=llm,
    verbose=True,
    max_iter=3,
)

# ─── TASKS ───────────────────────────────────────────────────────────────────

task_market = Task(
    description="""
    1. Use 'Get Overall Market Mood' tool to check Nifty, Bank Nifty, VIX
    2. If market mood is BEARISH, still scan but flag caution
    3. Use 'Scan Stocks for Swing Trading Setup' tool with sector='all'
    4. Return top 5 candidates with their scores and signals
    """,
    expected_output="Market mood summary + top 5 swing candidates with scores.",
    agent=market_agent,
)

task_research = Task(
    description="""
    Take the top 3 stocks from the market agent's findings.
    For each stock:
    1. Use 'Get Detailed Stock Analysis' tool
    2. Use 'Get Swing Trade News' tool
    3. Confirm or reject the swing setup based on combined analysis
    Pick the BEST 2-3 trades only. Quality over quantity.
    """,
    expected_output="Detailed analysis of top 2-3 confirmed swing trade setups.",
    agent=research_agent,
    context=[task_market],
)

task_report = Task(
    description=f"""
    Today's date: {datetime.now().strftime('%d %B %Y')}
    
    Create a swing trading report and send it via Telegram.
    
    Format EXACTLY like this:

    🇮🇳 SWING TRADE ALERT — {datetime.now().strftime('%d %b %Y')}
    ═══════════════════════════════

    🌡️ MARKET: [Bullish/Neutral/Bearish]
    Nifty: [level] | VIX: [level]

    ═══════════════════════════════
    📊 TODAY'S SWING TRADES
    ═══════════════════════════════

    🔹 TRADE 1: [TICKER]
    ▪ Entry: ₹[price]
    ▪ Stop Loss: ₹[price] ([%]% risk)
    ▪ Target: ₹[price] ([%]% gain)
    ▪ Hold: 2-5 days
    ▪ Risk/Reward: [X]:1
    ▪ Why: [one line reason]
    ▪ Confidence: High/Medium

    🔹 TRADE 2: [TICKER]
    ▪ Entry: ₹[price]
    ▪ Stop Loss: ₹[price] ([%]% risk)
    ▪ Target: ₹[price] ([%]% gain)
    ▪ Hold: 2-5 days
    ▪ Risk/Reward: [X]:1
    ▪ Why: [one line reason]
    ▪ Confidence: High/Medium

    ═══════════════════════════════
    💰 POSITION SIZING (₹10,000)
    ═══════════════════════════════
    ▪ Per trade: ₹3,000-5,000
    ▪ Max 2 trades at a time
    ▪ Never risk more than 2% per trade

    ═══════════════════════════════
    ⚠️ RULES
    ═══════════════════════════════
    ▪ Place limit orders only
    ▪ Set stop loss immediately after entry
    ▪ Do NOT average down
    ▪ Exit on target or stop loss — no emotions

    ⚠️ Research only. Not SEBI advice.

    After creating the report, use 'Send Telegram Report' tool to send it.
    """,
    expected_output="Formatted report sent to Telegram successfully.",
    agent=reporter_agent,
    context=[task_market, task_research],
)

# ─── CREW ────────────────────────────────────────────────────────────────────

crew = Crew(
    agents=[market_agent, research_agent, reporter_agent],
    tasks=[task_market, task_research, task_report],
    process=Process.sequential,
    verbose=True,
)

# ─── RUN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  📈 INDIAN SWING TRADING AI AGENT")
    print("  Nifty 500 | Telegram Alerts | ₹10k Capital")
    print("="*60 + "\n")

    result = crew.kickoff()

    print("\n" + "="*60)
    print("  ✅ SWING TRADING REPORT COMPLETE")
    print("="*60)
    print(result)

    # Save report
    filename = f"swing_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(result))
    print(f"\n✅ Report saved to {filename}")
