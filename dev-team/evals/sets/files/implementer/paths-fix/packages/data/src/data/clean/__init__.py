"""Collapse exact duplicate trades and sort them into a TradeTable."""

from data.clean.rules import CleanError, clean_trades

__all__ = ["CleanError", "clean_trades"]
