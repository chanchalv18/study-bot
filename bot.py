import os
import requests
import csv
import io
from datetime import datetime, date
import asyncio
from telegram import Bot

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")   # Set in GitHub Secrets
CHAT_ID         = os.environ.get("CHAT_ID")           # Set in GitHub Secrets
SHEET_ID        = "1qrcfO4ClkqAsLKYb5X2TfjoiS4w1xfTc2-Aa7wKSPt0"
PLAN_START_DATE = date(2026, 3, 24)

# ─────────────────────────────────────────
# FETCH DATA FROM GOOGLE SHEET
# ─────────────────────────────────────────
def fetch_topics():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    response = requests.get(url)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.text))
    return list(reader)

def get_current_day():
    delta = (date.today() - PLAN_START_DATE).days + 1
    return max(1, min(delta, 45))

def get_week_number(day):
    return min((day - 1) // 7 + 1, 6)

def is_weekend():
    return date.today().weekday() >= 5

def progress_bar(done, total):
    percent = int((done / total) * 100) if total > 0 else 0
    filled  = percent // 10
    bar     = "🟩" * filled + "⬜" * (10 - filled)
    return bar, percent

def build_daily_message(topics):
    current_day  = get_current_day()
    current_week = get_week_number(current_day)
    week_label   = f"Week {current_week}"
    today_str    = datetime.today().strftime("%A, %d %B %Y")
    today_row    = next((t for t in topics if t.get("Day", "").strip() == str(current_day)), None)
    week_topics  = [t for t in topics if t.get("Week", "").strip() == week_label]
    done_topics  = [t for t in week_topics if t.get("Status", "").strip().lower() == "done"]
    bar, percent = progress_bar(len(done_topics), len(week_topics))
    all_done     = [t for t in topics if t.get("Status", "").strip().lower() == "done"]
    overall_bar, overall_pct = progress_bar(len(all_done), 45)
    study_hours  = "5–6 hours" if is_weekend() else "2–3 hours"

    msg = []
    msg.append(f"📋 *Daily Study & Job Hunt Briefing*")
    msg.append(f"📆 {today_str}")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"")
    msg.append(f"🎯 *Today's Focus — Day {current_day} of 45*")
    msg.append(f"")
    if today_row:
        status   = today_row.get("Status", "Pending").strip().lower()
        topic    = today_row.get("Topic", "—")
        category = today_row.get("Category", "—")
        phase    = today_row.get("Phase", "—")
        week     = today_row.get("Week", "—")
        icon     = "✅" if status == "done" else "▶️"
        msg.append(f"{icon}  *Topic:* {topic}")
        msg.append(f"     *Category:* {category}")
        msg.append(f"     *Phase:* {phase}  |  {week}")
        msg.append(f"")
        if status == "done":
            msg.append(f"_You have already completed today's topic. Use this time to review or get ahead._")
        else:
            msg.append(f"_Mark this as Done in your Google Sheet once completed._")
    else:
        msg.append(f"🎉 You have completed all 45 days of the plan. Well done!")
    msg.append(f"")
    msg.append(f"⏱ *Suggested Time Split — {study_hours} today*")
    msg.append(f"  • Learning & study      — 60%")
    msg.append(f"  • Hands-on practice     — 30%")
    msg.append(f"  • Notes review          — 10%")
    msg.append(f"")
    msg.append(f"📊 *{week_label} Progress:* {bar}  {percent}%")
    msg.append(f"   {len(done_topics)} of {len(week_topics)} topics completed this week")
    msg.append(f"")
    pending = [t for t in week_topics if t.get("Status", "").strip().lower() != "done"]
    if pending:
        msg.append(f"📌 *Remaining Topics This Week:*")
        for t in pending:
            day_num = t.get("Day", "?")
            topic   = t.get("Topic", "")
            cat     = t.get("Category", "")
            marker  = "▶️" if t.get("Day", "").strip() == str(current_day) else "  •"
            msg.append(f"  {marker}  Day {day_num} — {topic}  _({cat})_")
        msg.append(f"")
    msg.append(f"📈 *Overall Plan Progress:* {overall_bar}  {overall_pct}%")
    msg.append(f"   {len(all_done)} of 45 topics completed")
    msg.append(f"")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"💼 *Daily Job Hunt Checklist*")
    msg.append(f"")
    msg.append(f"  ☐  Apply to 2–3 roles today")
    msg.append(f"  ☐  Search LinkedIn — filter: Remote | AI Solutions | Consultant")
    msg.append(f"  ☐  Follow up on any applications older than 7 days")
    msg.append(f"  ☐  Connect with 1 person at a target company")
    msg.append(f"")
    msg.append(f"*Target Roles:*  AI Solutions Consultant  |  Solutions Architect  |  Pre-Sales Engineer")
    msg.append(f"*Location Filter:*  Remote only 🌍")
    msg.append(f"")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"_End of day: Update your Google Sheet and mark completed topics as Done._")
    msg.append(f"_Consistency is the only strategy that works. Keep going._ 💪")
    return "\n".join(msg)

async def send_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
    print("✅ Message sent successfully!")

async def main():
    print("📊 Fetching data from Google Sheet...")
    topics = fetch_topics()
    print(f"✅ {len(topics)} topics loaded")
    message = build_daily_message(topics)
    print(message)
    await send_message(message)

if __name__ == "__main__":
    asyncio.run(main())
