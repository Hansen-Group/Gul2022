#!/usr/bin/python3
#
# Copyright (c) 2012 Mikkel Schubert <MikkelSch@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import itertools
from typing import (
    Any,
    AnyStr,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

T = TypeVar("T")


class TableError(RuntimeError):
    pass


def format_timespan(seconds: float):
    if seconds < 60:
        return "{:.1f}s".format(seconds)
    elif seconds < 3600:
        return "{:.0f}:{:02.0f}s".format(seconds // 60, seconds % 60)
    else:
        return "{:.0f}:{:02.0f}:{:02.0f}s".format(
            seconds // 3600,
            (seconds % 3600) // 60,
            seconds % 60,
        )


def padded_table(
    table: Iterable[Union[str, Iterable[Any]]],
    min_padding: int = 4,
) -> Iterator[str]:
    """Takes a sequence of iterables, each of which represents a row in a
    table. Values are converted to string, and padded with whitespace such that
    each column is separated from its adjacent columns by at least 4 spaces.
    Empty cells or whitespace in values are not allowed.

    If a string is included instead of a row, this value is added as is. Note
    that these lines should be whitespace only, or start with a '#' if the
    resulting table is to be readable with 'parse_padded_table'.
    """
    str_rows: List[Union[str, List[str]]] = []
    max_sizes: List[int] = []
    for row in table:
        if not isinstance(row, str):
            row = list(map(str, row))
            row_sizes = list(map(len, row))
            max_sizes = list(
                map(max, itertools.zip_longest(max_sizes, row_sizes, fillvalue=0))
            )

        str_rows.append(row)

    sizes = [(size + min_padding) for size in max_sizes]
    for row in str_rows:
        if not isinstance(row, str):
            row = "".join(
                field.ljust(padding) for (field, padding) in zip(row, sizes)
            ).rstrip()
        yield row


def parse_padded_table(
    lines: Iterable[str],
    header: Optional[List[str]] = None,
) -> Iterator[Dict[str, str]]:
    """Parses a padded table generated using 'padded_table', or any table which
    consists of a fixed number of columns seperated by whitespace, with no
    whitespace in the cells. Empty lines and lines starting with '#' (comments)
    are ignored. Each row is returned as a dictionary, using the values found
    in the first row as keys.
    """
    nheader = -1
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        elif header is None:
            header = stripped.split()
            nheader = len(header)
            continue

        fields = stripped.split()
        if len(fields) != nheader:
            raise TableError(
                "Malformed table; #columns does not match header:"
                " %r vs %r" % (header, fields)
            )

        yield dict(zip(header, fields))


def parse_lines(
    lines: Iterable[AnyStr],
    parser: Callable[[AnyStr, int], T],
) -> Iterator[T]:
    """Parses a set of lines using the supplied callable:
        lambda (line, length): ...

    Supports the parser functions available in 'pysam': asGTF, asBED, etc.
    """
    if not callable(parser):
        raise TypeError("'parser' must be a callable, not %r" % (parser,))

    for line in lines:
        stripped = line.lstrip()
        if stripped and stripped[0] not in ("#", 35):
            stripped = line.rstrip()
            yield parser(stripped, len(stripped))


def parse_lines_by_contig(
    lines: Iterable[AnyStr],
    parser: Callable[[AnyStr, int], T],
) -> Dict[str, List[T]]:
    """Reads the lines of a text file, parsing each line with the specified
    parser, and aggregating results by the 'contig' property of reach record.
    """
    table: Dict[str, List[Any]] = {}
    for record in parse_lines(lines, parser):
        try:
            table[cast(Any, record).contig].append(record)
        except KeyError:
            table[cast(Any, record).contig] = [record]

    return table
