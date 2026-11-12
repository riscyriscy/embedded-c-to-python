"""A helper module with a deprecated call, like many vendor and in-house libraries."""

import datetime


def stamp() -> str:
    return datetime.datetime.utcnow().strftime("%H:%M:%S")  # deprecated since Python 3.12
