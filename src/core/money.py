from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MONEY_QUANT = Decimal("0.01")


def to_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, Decimal):
        dec = value
    else:
        dec = Decimal(str(value))
    return dec.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def to_minor_units(value: Decimal | str | int | float) -> int:
    dec = to_decimal(value)
    return int((dec * 100).to_integral_value(rounding=ROUND_HALF_UP))


def from_minor_units(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
