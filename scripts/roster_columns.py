"""Header-based access for the roster CSV.

The Numbers roster sheet is edited by humans, so non-stat columns may be inserted
between the career totals and season blocks.  Consumers must never rely on the
physical column positions of season fields.
"""

from __future__ import annotations

from typing import Iterable


def header_index(headers: Iterable[str]) -> dict[str, int]:
    """Return a trimmed header name -> CSV index map, rejecting duplicate names."""
    result: dict[str, int] = {}
    for index, raw in enumerate(headers):
        name = raw.strip()
        if name and name not in result:
            result[name] = index
    return result


def column(columns: dict[str, int], name: str) -> int | None:
    """Return the requested column index, or None for optional/missing columns."""
    return columns.get(name)


def value(row: list[str], columns: dict[str, int], name: str) -> str:
    """Safely fetch a named column value from a roster row."""
    index = column(columns, name)
    return row[index].strip() if index is not None and index < len(row) else ""


def season_columns(columns: dict[str, int], year: int | str) -> tuple[int | None, int | None, int | None, int | None]:
    """Return (apps, goals, assists, rating) indexes for one season by header."""
    prefix = str(year)
    return (
        column(columns, f"{prefix}出场"),
        column(columns, f"{prefix}进球"),
        column(columns, f"{prefix}助攻"),
        column(columns, f"{prefix}团队分"),
    )
