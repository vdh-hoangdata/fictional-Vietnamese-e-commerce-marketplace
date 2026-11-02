import pytest

from src.business_rules.finance import TERMINAL, TRANSITIONS, allocate, returned_value
from src.config.settings import PRESETS, Settings
from src.utils.core import START, VN, rng, stamp


def test_largest_remainder_conserves_vnd():
    assert allocate(10, [7, 7, 7]) == [4, 3, 3]
    random = rng(19, "allocation_test")
    for _ in range(200):
        weights = [random.randrange(1000000) for _ in range(5)]
        amount = random.randrange(sum(weights) + 1)
        result = allocate(amount, weights)
        assert sum(result) == amount
        assert all(0 <= share <= weight for share, weight in zip(result, weights))


def test_allocation_edge_cases():
    assert allocate(0, [0, 0]) == [0, 0]
    assert allocate(12, [5, 7]) == [5, 7]
    with pytest.raises(ValueError):
        allocate(13, [5, 7])


def test_partial_refund_rounding():
    assert returned_value(100001, 3, 1) == 33333
    assert returned_value(100001, 3, 3) == 100001
    with pytest.raises(ValueError):
        returned_value(100, 1, 2)


def test_named_random_streams_are_isolated():
    expected = [rng(42, "orders").random(), rng(42, "prices").random()]
    for _ in range(100):
        rng(42, "new_table").random()
    assert expected == [rng(42, "orders").random(), rng(42, "prices").random()]
    assert expected[0] != expected[1]


def test_utc_and_local_midnight():
    assert stamp(START) == "2023-12-31T17:00:00Z"
    assert str(START.astimezone(VN).date()) == "2024-01-01"


def test_terminal_states_do_not_reopen():
    assert all(state not in TRANSITIONS for state in TERMINAL)
    assert "delivered" not in TRANSITIONS["created"]


@pytest.mark.parametrize("field,value", [("return_rate", -1), ("payment_failure_rate", 1.2), ("chunk_rows", 0), ("size", "tiny"), ("profile", "unknown")])
def test_config_rejects_invalid_parameters(field, value):
    settings = Settings()
    setattr(settings, field, value)
    with pytest.raises(ValueError):
        settings.validate()


def test_presets_preserve_requested_volumes():
    assert Settings().counts["orders"] == 100000
    assert PRESETS["small"]["orders"] == 5000
    assert PRESETS["large"]["orders"] == 1000000
