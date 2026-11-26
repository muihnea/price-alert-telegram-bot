import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from price import get_price

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "tracked.json"
CHECK_INTERVAL = 1800  # seconds  # seconds, for testing. Use 1800 (30 min) for real use.


def load_items():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_items(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a price alert bot. Send /help to see what I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - say hello\n"
        "/help - show this message\n"
        "/track <url> - alert me when the price drops\n"
        "/list - show what I'm tracking"
    )


async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track <url>")
        return

    url = context.args[0]
    try:
        price = await asyncio.to_thread(get_price, url)
    except Exception:
        await update.message.reply_text("Sorry, I couldn't read a price from that page.")
        return

    items = load_items()
    chat_id = update.effective_chat.id
    if any(i["chat_id"] == chat_id and i["url"] == url for i in items):
        await update.message.reply_text("You're already tracking this link.")
        return
    items.append({"chat_id": chat_id, "url": url, "price": price})
    save_items(items)
    await update.message.reply_text(f"Tracking it. Current price: {price}")


async def list_tracked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mine = [i for i in load_items() if i["chat_id"] == chat_id]
    if not mine:
        await update.message.reply_text("You're not tracking anything yet.")
        return
    lines = [f"{i['price']} - {i['url']}" for i in mine]
    await update.message.reply_text("\n".join(lines))


async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    items = load_items()
    for item in items:
        try:
            new_price = await asyncio.to_thread(get_price, item["url"])
        except Exception:
            continue
        if new_price < item["price"]:
            await context.bot.send_message(
                chat_id=item["chat_id"],
                text=f"Price drop! {item['price']} -> {new_price}\n{item['url']}",
            )
        item["price"] = new_price
    save_items(items)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("list", list_tracked))
    app.job_queue.run_repeating(check_prices, interval=CHECK_INTERVAL, first=10)
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()