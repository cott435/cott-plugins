"""Render the daily report from a feature frame."""

import argparse
from datetime import date, timedelta

import pandas as pd
from jinja2 import Template

from analysis.features.build import FEATURE_COLUMNS, build_features
from data.clean.rules import BAR_COLUMNS

TEMPLATE = Template(
    "# {{ symbol }} — {{ run_date }}\n\n"
    "bar columns: {{ bar_columns | join(', ') }}\n"
    "feature columns: {{ feature_columns | join(', ') }}\n\n"
    "latest 1d return: {{ ret }}\nlatest 20d vol: {{ vol }}\n"
)


def render_report(symbol: str, run_date: date, features: pd.DataFrame) -> str:
    latest = features.dropna().iloc[-1]
    return TEMPLATE.render(
        symbol=symbol,
        run_date=run_date.isoformat(),
        bar_columns=BAR_COLUMNS,
        feature_columns=FEATURE_COLUMNS,
        ret=f"{latest['ret_1d']:.4f}",
        vol=f"{latest['vol_20d']:.4f}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="analysis-report")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--run-date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    start = args.run_date - timedelta(days=60)
    print(render_report(args.symbol, args.run_date, build_features(args.symbol, start, args.run_date)))
