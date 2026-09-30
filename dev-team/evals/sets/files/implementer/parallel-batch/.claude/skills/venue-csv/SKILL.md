---
name: venue-csv
description: The XVEN venue's daily trade export dialect — its header comments, delimiter, column names, side codes and quantity format. Use when writing or changing code that reads an XVEN export file.
---

# Reading an XVEN export

An XVEN export is a UTF-8 text file, one trade per line. Every export the venue has produced
follows these rules; code that reads one follows all of them.

1. **Comment lines.** The file opens with lines starting `#` (`# venue=XVEN`,
   `# exported=2026-09-29T18:00:00+02:00`), and the venue inserts a `# rows=<n>` checkpoint
   line every few thousand rows. Skip every line whose first character is `#`, wherever it
   appears. Never hand one to the CSV reader.
2. **Delimiter.** `;`, not `,`. Fields are never quoted.
3. **Columns.** The first line that is not a comment is the header row:
   `TradeTime;Ticker;Px;Qty;Side`. Map `TradeTime` → `ts`, `Ticker` → `symbol`, `Px` →
   `price`, `Qty` → `size`, `Side` → `side`. A missing column is an error naming the file and
   the header row's line number.
4. **Side codes.** `B` is a buy and `S` a sell, mapped to `"buy"` and `"sell"`. Any other
   code is an error naming the file and the line.
5. **Quantity.** `Qty` may carry an apostrophe as a thousands separator (`1'200`). Remove
   every `'` before parsing it as an integer.
6. **Price.** `Px` uses `.` as the decimal point and never a separator.
7. **TradeTime.** Day first (`29.09.2026 14:03:07 +02:00`), always with the venue's UTC
   offset. Parse it with the repo's decided parser and convert it to UTC.

## Line numbers

An error's line number is the physical line in the file, 1-based, comment lines included —
the number an editor shows, so a user can open the file at it.

## Checks

- A file holding only comment lines and the header row is valid: zero trades.
- Reading `1'200` as `1` or `200` is the classic mistake; test a separator-bearing `Qty`.
