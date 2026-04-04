import os
import requests
import csv
import io
from datetime import datetime, date, timezone, timedelta
import asyncio
from telegram import Bot

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")   # Set in GitHub Secrets
CHAT_ID         = os.environ.get("CHAT_ID")           # Set in GitHub Secrets
SHEET_ID        = "1qrcfO4ClkqAsLKYb5X2TfjoiS4w1xfTc2-Aa7wKSPt0"
PLAN_START_DATE = date(2026, 4, 5)  # Update this to your actual start date
IST = timezone(timedelta(hours=5, minutes=30))  # IST = UTC + 5:30

# ─────────────────────────────────────────
# FETCH DATA FROM GOOGLE SHEET
# ─────────────────────────────────────────
def fetch_topics():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    response = requests.get(url)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.text))
    return list(reader)

# ─────────────────────────────────────────
# DATE & PROGRESS HELPERS
# ─────────────────────────────────────────
def get_current_day():
    today_ist = datetime.now(IST).date()
    delta = (today_ist - PLAN_START_DATE).days + 1
    return max(1, min(delta, 45))

def get_week_number(day):
    return min((day - 1) // 7 + 1, 6)

def is_weekend():
    return datetime.now(IST).weekday() >= 5

def progress_bar(done, total):
    percent = int((done / total) * 100) if total > 0 else 0
    filled  = percent // 10
    bar     = "🟩" * filled + "⬜" * (10 - filled)
    return bar, percent

# ─────────────────────────────────────────
# BUILD MESSAGE
# ─────────────────────────────────────────
def build_daily_message(topics):
    current_day  = get_current_day()
    current_week = get_week_number(current_day)
    week_label   = f"Week {current_week}"
    today_str    = datetime.now(IST).strftime("%A, %d %B %Y")

    # Today's topic from sheet
    today_row = next((t for t in topics if t.get("Day", "").strip() == str(current_day)), None)

    # Week-level progress
    week_topics  = [t for t in topics if t.get("Week", "").strip() == week_label]
    done_topics  = [t for t in week_topics if t.get("Status", "").strip().lower() == "done"]
    bar, percent = progress_bar(len(done_topics), len(week_topics))

    # Overall plan progress
    all_done     = [t for t in topics if t.get("Status", "").strip().lower() == "done"]
    overall_bar, overall_pct = progress_bar(len(all_done), 45)

    # Time guidance
    study_hours = "5–6 hours" if is_weekend() else "2–3 hours"

    msg = []

    # ── Header ──
    msg.append(f"📋 *Daily Study & Job Hunt Briefing*")
    msg.append(f"📆 {today_str}")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"")

    # ── Today's Study Focus ──
    msg.append(f"🎯 *Today's Study Focus — Day {current_day} of 45*")
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

    # ── Suggested Time Split ──
    msg.append(f"⏱ *Suggested Time Split — {study_hours} today*")
    msg.append(f"  • Learning & study      — 60%")
    msg.append(f"  • Hands-on practice     — 30%")
    msg.append(f"  • Notes review          — 10%")
    msg.append(f"")

    # ── Week Progress ──
    msg.append(f"📊 *{week_label} Progress:* {bar}  {percent}%")
    msg.append(f"   {len(done_topics)} of {len(week_topics)} topics completed this week")
    msg.append(f"")

    # ── Remaining topics this week ──
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

    # ── Overall Plan Progress ──
    msg.append(f"📈 *Overall Plan Progress:* {overall_bar}  {overall_pct}%")
    msg.append(f"   {len(all_done)} of 45 topics completed")
    msg.append(f"")

    # ── Job Hunt Checklist ──
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"💼 *Daily Job Hunt Checklist*")
    msg.append(f"")
    msg.append(f"  ☐  Apply to 2–3 roles today")
    msg.append(f"  ☐  Search LinkedIn — filter: Remote | AI Solutions | Consultant")
    msg.append(f"  ☐  Follow up on any applications older than 7 days")
    msg.append(f"  ☐  Connect with 1 person at a target company")
    msg.append(f"")
    msg.append(f"*Target Roles:*  AI Solutions Consultant  |  Solutions Architect  |  Pre-Sales Engineer")
    msg.append(f"*Target Companies:*  AI Startups  |  SaaS Platforms  |  Consulting Firms")
    msg.append(f"*Location Filter:*  Remote only 🌍")
    msg.append(f"")

    # ── Footer ──
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"_End of day: Update your Google Sheet and mark completed topics as Done._")
    msg.append(f"_Consistency is the only strategy that works. Keep going._ 💪")

    return "\n".join(msg)

# ─────────────────────────────────────────
# EVENING REMINDER MESSAGE
# ─────────────────────────────────────────
def build_evening_message(topics):
    current_day  = get_current_day()
    current_week = get_week_number(current_day)
    week_label   = f"Week {current_week}"

    today_row   = next((t for t in topics if t.get("Day", "").strip() == str(current_day)), None)
    week_topics = [t for t in topics if t.get("Week", "").strip() == week_label]
    done_topics = [t for t in week_topics if t.get("Status", "").strip().lower() == "done"]
    bar, percent = progress_bar(len(done_topics), len(week_topics))
    today_done  = today_row and today_row.get("Status", "").strip().lower() == "done"

    msg = []
    msg.append(f"🌙 *Evening Check-in — Day {current_day} of 45*")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"")

    if today_row:
        topic = today_row.get("Topic", "—")
        if today_done:
            msg.append(f"✅ *Today\'s topic is marked Done — great work!*")
            msg.append(f"   _{topic}_")
        else:
            msg.append(f"⚠️ *Today\'s topic is still Pending:*")
            msg.append(f"   _{topic}_")
            msg.append(f"")
            msg.append(f"Please update your Google Sheet if you completed it today.")
    msg.append(f"")
    msg.append(f"📊 *{week_label} Progress:* {bar}  {percent}%")
    msg.append(f"   {len(done_topics)} of {len(week_topics)} topics completed this week")
    msg.append(f"")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"📝 *End of Day Checklist:*")
    msg.append(f"")
    msg.append(f"  ☐  Mark today\'s topic as Done in Google Sheet")
    msg.append(f"  ☐  Note down 1 thing you learned today")
    msg.append(f"  ☐  Check if any job applications need follow-up")
    msg.append(f"  ☐  Prep for tomorrow — Day {min(current_day + 1, 45)}")
    msg.append(f"")
    msg.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    msg.append(f"_Rest well. Tomorrow\'s morning briefing arrives at 9:30 AM._ 🌅")

    return "\n".join(msg)

# ─────────────────────────────────────────
# SEND TO TELEGRAM
# ─────────────────────────────────────────
async def send_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode="Markdown"
    )
    print("✅ Message sent successfully!")

# ─────────────────────────────────────────
# MAIN — mode: morning or evening
# ─────────────────────────────────────────
async def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"

    print("📊 Fetching data from Google Sheet...")
    topics = fetch_topics()
    print(f"✅ {len(topics)} topics loaded")

    if mode == "evening":
        print("🌙 Building evening reminder...")
        message = build_evening_message(topics)
    else:
        print("🌅 Building morning briefing...")
        message = build_daily_message(topics)

    print("\n--- MESSAGE PREVIEW ---")
    print(message)
    print("─────────────────────\n")

    print("📤 Sending to Telegram...")
    await send_message(message)

if __name__ == "__main__":
    asyncio.run(main())
