# BitMEX EMA Bot

A simple trading bot for BitMEX that enters long positions when the last price exceeds the exponential moving average (EMA).

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your BitMEX API keys.

```bash
cp .env.example .env
```

3. Run the bot:

```bash
python bitmex_ema_bot.py
```

## Tests

Run unit tests with:

```bash
pytest
```
