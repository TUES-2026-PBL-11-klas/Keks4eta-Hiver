import pytest

from domain.entities.transaction import Transaction, TransactionStatus
from domain.errors.domain_errors import (
    EscrowAlreadyReleasedError,
    TaskNotCompletedError,
)
from domain.value_objects.money import Money


def make_escrow(price=Money.of(100)) -> Transaction:
    return Transaction.create_for_task(
        id="tx1",
        task_id="t1",
        client_id="c1",
        hiver_id="h1",
        offer_price=price,
        stripe_payment_intent_id="pi_test",
    )


class TestTransactionFactory:
    def test_create_for_task_computes_fee_and_payout(self):
        tx = make_escrow(Money.of(100))
        assert tx.gross_amount == Money.of(100)
        assert tx.platform_fee == Money.of(10)
        assert tx.hiver_payout == Money.of(90)
        assert tx.is_held()


class TestEscrowRelease:
    def test_release_moves_held_to_released(self):
        tx = make_escrow()
        tx.release()
        assert tx.is_released()
        assert tx.released_at is not None

    def test_double_release_rejected(self):
        tx = make_escrow()
        tx.release()
        with pytest.raises(EscrowAlreadyReleasedError):
            tx.release()

    def test_release_after_refund_rejected(self):
        tx = make_escrow()
        tx.refund()
        with pytest.raises(TaskNotCompletedError):
            tx.release()


class TestEscrowRefund:
    def test_refund_moves_to_refunded(self):
        tx = make_escrow()
        tx.refund()
        assert tx.status == TransactionStatus.REFUNDED
        assert tx.refunded_at is not None

    def test_refund_after_release_rejected(self):
        tx = make_escrow()
        tx.release()
        with pytest.raises(EscrowAlreadyReleasedError):
            tx.refund()
