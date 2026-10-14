"""Small business rules with obvious boundaries to experiment with."""

FREE_SHIPPING_THRESHOLD_CENTS = 5_000
SHIPPING_FEE_CENTS = 500


def shipping_quote(subtotal_cents: int) -> dict[str, int]:
    """Use integer cents to avoid floating point rounding in money calculations."""
    if type(subtotal_cents) is not int or subtotal_cents < 0:
        raise ValueError("subtotal_cents must be a non-negative integer")

    shipping_cents = 0 if subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS else SHIPPING_FEE_CENTS
    return {
        "subtotal_cents": subtotal_cents,
        "shipping_cents": shipping_cents,
        "total_cents": subtotal_cents + shipping_cents,
    }
