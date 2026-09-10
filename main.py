import sqlite3
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8050058104:AAFKaOVkw3R00CXLZ0oi7jFdtHvd1IJ_cak"
ADMIN_USER_ID = 8269505378

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

DB_NAME = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_mappings (
            admin_msg_id INTEGER,
            channel_id TEXT,
            channel_msg_id INTEGER,
            PRIMARY KEY (admin_msg_id, channel_id)
        )
    """)
    default_channels = [
        ("@BenSmithMarketEducation", "Ben Smith Market Education"),
        ("@SohailProfessorTrader", "Sohail Professor Trader"),
        ("@MTechnicalpipshuk5", "M Technical Pips"),
        ("@SMC_LogicAcademy", "SMC Logic Academy"),
        ("@ApexcapitalFX100", "Apex Capital FX"),
        ("@TomTradesGoldMaster", "Tom Trades Gold Master"),
        ("@larik101", "Larik 101")
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?, ?)",
        default_channels
    )
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, channel_name FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_message_mapping(admin_msg_id, channel_id, channel_msg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO signal_mappings (admin_msg_id, channel_id, channel_msg_id) VALUES (?, ?, ?)",
        (admin_msg_id, channel_id, channel_msg_id)
    )
    conn.commit()
    conn.close()

def get_channel_msg_mappings(admin_reply_to_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT channel_id, channel_msg_id FROM signal_mappings WHERE admin_msg_id = ?",
        (admin_reply_to_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    await update.message.reply_text("✅ Signal Bot Active on Render! Send any text or photo to broadcast.")

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return

    channels = get_channels()
    if not channels:
        await update.message.reply_text("⚠️ No channels configured.")
        return

    admin_msg_id = update.message.message_id
    is_reply = update.message.reply_to_message is not None

    mappings = {}
    if is_reply:
        parent_admin_msg_id = update.message.reply_to_message.message_id
        mappings = get_channel_msg_mappings(parent_admin_msg_id)

    report = ["<b>Broadcast Status:</b>\n"]

    for ch_id, ch_name in channels:
        try:
            reply_to = mappings.get(ch_id) if is_reply else None

            sent_msg = await context.bot.copy_message(
                chat_id=ch_id,
                from_chat_id=update.effective_chat.id,
                message_id=admin_msg_id,
                reply_to_message_id=reply_to
            )
            save_message_mapping(admin_msg_id, ch_id, sent_msg.message_id)
            report.append(f"✓ Sent to {ch_name}")
        except Exception as e:
            report.append(f"✗ Failed for {ch_name}: {str(e)}")

    await update.message.reply_text("\n".join(report), parse_mode="HTML")

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO) & ~filters.COMMAND,
        handle_incoming_message
    ))
    print("Signal Bot Running on Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
