import importlib.util
import pathlib
import pytest

spec = importlib.util.spec_from_file_location(
    "bot",
    pathlib.Path(__file__).resolve().parents[1] / "bitmex_ema_bot.py",
)
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


def test_calculate_ema():
    closes = [1, 2, 3, 4, 5]
    result = bot.calculate_ema(closes, alpha=0.5)
    assert pytest.approx(result, rel=1e-2) == 4.16
