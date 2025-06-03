#!/usr/bin/env python3
"""Simple EMA based trading bot for BitMEX."""

import json
import logging
import os
import time
from datetime import datetime, timedelta

import ccxt
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Trading parameters can be overridden with environment variables
LOT = int(os.getenv("LOT", 100))
CLOSE_RANGE = int(os.getenv("CLOSE_RANGE", 30))
STOP_RANGE = int(os.getenv("STOP_RANGE", 20))

bitmex = ccxt.bitmex({
    "apiKey": os.getenv("BITMEX_API_KEY", ""),
    "secret": os.getenv("BITMEX_API_SECRET", ""),
})

# Use testnet if BITMEX_TESTNET=1
if os.getenv("BITMEX_TESTNET") == "1":
    bitmex.urls["api"] = bitmex.urls["test"]

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def limit(side: str, price: float, size: int):
    """Place a limit order."""
    return bitmex.create_order(
        "BTC/USD", type="limit", side=side, price=price, amount=size
    )


def market(side: str, size: int):
    """Place a market order."""
    return bitmex.create_order("BTC/USD", type="market", side=side, amount=size)


def fetch_candles():
    """Fetch recent candles from Cryptowatch."""
    after = (datetime.now() - timedelta(minutes=10)).strftime("%s")
    query = {"periods": "60", "after": after}
    resp = requests.get(
        "https://api.cryptowat.ch/markets/bitmex/btcusd-perpetual-futures/ohlc",
        params=query,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["result"]["60"]


def calculate_ema(closes, alpha: float = 0.15) -> float:
    """Return the last EMA value from a list of closes."""
    df = pd.DataFrame({"close": closes})
    return df["close"].ewm(alpha=alpha).mean().iloc[-1]


def get_ema() -> float:
    """Retrieve candles and compute EMA."""
    rows = fetch_candles()
    closes = [r[4] for r in rows]
    return calculate_ema(closes)

def run() -> None:
    """Main trading loop."""
    entry_price = 0
    open_id = ""
    close_id = ""

    while True:
        try:
            logger.info(
                "entryPrice=%s openId=%s closeId=%s", entry_price, open_id, close_id
            )
            last = bitmex.fetch_ticker("BTC/USD")["last"]
            logger.info("last price: %s", last)

            open_orders = bitmex.fetch_open_orders()
            position = bitmex.private_get_position()

            if not open_orders:
                if not position or position[0]["currentQty"] == 0:
                    ema = get_ema()
                    logger.info("ema: %s", ema)
                    if last >= ema:
                        entry_price = last - 2
                        order = limit("buy", entry_price, LOT)
                        open_id = order["id"]
                        logger.info("buy entry: %s", order)
                elif position[0]["currentQty"] >= LOT:
                    order = limit("sell", entry_price + CLOSE_RANGE, LOT)
                    close_id = order["id"]
                    logger.info("position close: %s", order)

            if position and position[0]["currentQty"] >= LOT and last <= (
                entry_price - STOP_RANGE
            ):
                market("sell", LOT)
                logger.info("loss cut")
                bitmex.cancel_order(close_id)

            if open_orders and open_orders[0]["id"] == open_id:
                order_time = datetime.fromtimestamp(
                    int(str(open_orders[0]["timestamp"])[0:10])
                )
                if datetime.now() - timedelta(minutes=1) > order_time:
                    bitmex.cancel_order(open_id)
                    logger.info("order cancel")

        except Exception as e:  # pragma: no cover - network errors
            logger.error("error: %s", e)

        time.sleep(10)



if __name__ == "__main__":
    run()

