"""Intent tests for the `clean_bars` interface (design §5, §6)."""

import logging

import pandas as pd
import pytest

from data.clean.api import CleanResult, clean_bars
from data.clean.errors import EmptyBars, MissingColumns


def test_missing_column_raises(bars):
    """Design §6 a REQUIRED column absent: MissingColumns names the missing column."""
    with pytest.raises(MissingColumns) as info:
        clean_bars(bars.drop(columns=["volume"]))
    assert info.value.missing == ["volume"]


def test_empty_frame_raises(bars):
    """Design §6 df has no rows: EmptyBars."""
    with pytest.raises(EmptyBars):
        clean_bars(bars.iloc[0:0])


def test_output_columns_unchanged(bars):
    """Design §5 clean_bars: result.bars has the input's columns, in order."""
    result = clean_bars(bars)
    assert isinstance(result, CleanResult)
    assert list(result.bars.columns) == list(bars.columns)


def test_gaps_filled_counts_inserted_rows(bars):
    """Design §5 CleanResult: gaps_filled is the number of rows step 4 inserted."""
    result = clean_bars(bars)
    assert result.gaps_filled == 2


def test_does_not_mutate_input(bars):
    """Design §5 clean_bars: the argument is never mutated."""
    before = bars.copy()
    clean_bars(bars)
    pd.testing.assert_frame_equal(bars, before)


def test_logs_done_event(bars, caplog):
    """Design §6 done: one data.clean.done event with rows_in, rows_out, gaps_filled."""
    with caplog.at_level(logging.INFO, logger="data.clean"):
        clean_bars(bars)
    records = [r for r in caplog.records if r.getMessage() == "data.clean.done"]
    assert len(records) == 1
    record = records[0]
    assert record.rows_in == 5
    assert record.rows_out == 5
    assert record.gaps_filled == 2
