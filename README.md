# Price Alert Telegram Bot

A Telegram bot that tracks product prices and messages you when the price drops.

## Features

- `/track <url>` starts tracking a product page
- `/list` shows what you're tracking
- Checks every tracked link every 30 minutes and sends an alert when the price goes down
- Reads prices from standard page data (JSON-LD, meta tags, `itemprop`), so it works on many shops without custom code
- Handles formats like `1.299,99` and `1,299.99`
- Refuses duplicate links

## Tested on

- eMAG (emag.ro)
- books.toscrape.com (practice site)

Shops that load prices with JavaScript or block scripts may not work.

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram and copy the token.
2. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/muihnea/price-alert-telegram-bot.git
   cd price-alert-telegram-bot
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Mac/Linux
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste your token:
   ```
   BOT_TOKEN=your_token_here
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

```
/track https://www.emag.ro/.../pd/XXXXX/
/list
```

## Files

- `bot.py` - Telegram commands and the scheduled price check
- `price.py` - price extraction from product pages
- `tracked.json` - saved links (created automatically, not committed)

## Tech

Python, python-telegram-bot, requests, BeautifulSoup