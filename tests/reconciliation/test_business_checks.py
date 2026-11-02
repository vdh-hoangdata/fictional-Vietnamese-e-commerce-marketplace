import pytest

from src.validators.checks import run_sql_checks


@pytest.mark.parametrize("check", ["item_financials", "order_financials", "discount_reconciliation", "coupon_eligibility", "payment_reconciliation", "unique_collected_payment", "cod_settlement_chronology", "refund_limits", "refund_chronology", "refund_return_value", "return_eligibility", "return_quantity_limits", "purchase_linkage"])
def test_reconciliation_invariants(report, check):
    assert report["business_checks"][check] == 0


def test_validation_detects_corrupt_header_without_repair(database):
    database.execute("SAVEPOINT corrupt_header")
    try:
        before = database.execute("SELECT total_payable FROM orders WHERE order_id=1").fetchone()[0]
        database.execute("UPDATE orders SET total_payable=total_payable+1 WHERE order_id=1")
        errors = []
        result = run_sql_checks(database, errors)
        assert result["order_financials"] == 1
        assert database.execute("SELECT total_payable FROM orders WHERE order_id=1").fetchone()[0] == before + 1
    finally:
        database.execute("ROLLBACK TO corrupt_header")
        database.execute("RELEASE corrupt_header")


def test_validation_detects_negative_stock(database):
    database.execute("SAVEPOINT corrupt_stock")
    try:
        database.execute("UPDATE inventory_movements SET quantity_delta=-100000 WHERE movement_id=1")
        result = run_sql_checks(database, [])
        assert result["inventory_balances"] > 0
        assert result["inventory_movement_semantics"] > 0
    finally:
        database.execute("ROLLBACK TO corrupt_stock")
        database.execute("RELEASE corrupt_stock")
