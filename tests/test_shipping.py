import pytest

from cicd_demo.shipping import shipping_quote


@pytest.mark.parametrize(
    ("subtotal", "shipping", "total"),
    [(0, 500, 500), (1, 500, 501), (4999, 500, 5499), (5000, 0, 5000), (5001, 0, 5001)],
)
def test_shipping_boundaries(subtotal, shipping, total):
    assert shipping_quote(subtotal) == {
        "subtotal_cents": subtotal,
        "shipping_cents": shipping,
        "total_cents": total,
    }


@pytest.mark.parametrize("subtotal", [-1, 12.5, "5000", None, True, False])
def test_invalid_subtotals_are_rejected(subtotal):
    with pytest.raises(ValueError, match="non-negative integer"):
        shipping_quote(subtotal)
