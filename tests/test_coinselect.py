import random

import pytest

from coinselect.algorithms import bnb, knapsack, largest_first, srd
from coinselect.metrics import waste
from coinselect.models import (
    DUST_THRESHOLD,
    INPUT_VBYTES,
    SelectionResult,
    TxContext,
    UTXO,
    Wallet,
)


def ctx(target, feerate=10.0, ltf=10.0):
    return TxContext(target=target, feerate=feerate, long_term_feerate=ltf)


class TestModels:
    def test_effective_value(self):
        u = UTXO(value=100_000)
        assert u.effective_value(10.0) == 100_000 - round(INPUT_VBYTES * 10)

    def test_wallet_receive_spend(self):
        w = Wallet()
        a, b = w.receive(50_000), w.receive(30_000)
        assert w.balance == 80_000
        w.spend([a])
        assert w.utxos == [b]

    def test_result_with_change(self):
        c = ctx(50_000)
        u = UTXO(value=200_000)
        r = SelectionResult.build("t", c, [u])
        assert r.change > DUST_THRESHOLD
        # conservation: inputs = target + change + fee
        assert u.value == c.target + r.change + r.fee

    def test_dust_change_burned_to_fee(self):
        c = ctx(50_000)
        # value just barely above what's needed -> surplus below dust
        needed = c.selection_target + round(INPUT_VBYTES * c.feerate)
        u = UTXO(value=needed + 100)
        r = SelectionResult.build("t", c, [u])
        assert r.changeless and r.excess == 100
        assert u.value == c.target + r.fee

    def test_underfunded_selection_raises(self):
        c = ctx(100_000)
        with pytest.raises(ValueError):
            SelectionResult.build("t", c, [UTXO(value=50_000)])


class TestAlgorithms:
    def test_largest_first_prefers_big_coins(self):
        utxos = [UTXO(value=v) for v in (10_000, 500_000, 40_000)]
        sel = largest_first.select(utxos, ctx(100_000))
        assert [u.value for u in sel] == [500_000]

    def test_srd_funds_target(self):
        rng = random.Random(7)
        utxos = [UTXO(value=50_000) for _ in range(20)]
        c = ctx(120_000)
        sel = srd.select(utxos, c, rng)
        eff = sum(u.effective_value(c.feerate) for u in sel)
        assert eff >= c.selection_target

    def test_knapsack_funds_target(self):
        rng = random.Random(7)
        utxos = [UTXO(value=random.Random(1).randint(5_000, 90_000)) for _ in range(30)]
        c = ctx(150_000)
        sel = knapsack.select(utxos, c, rng)
        eff = sum(u.effective_value(c.feerate) for u in sel)
        assert eff >= c.selection_target

    def test_bnb_finds_exact_match(self):
        c = ctx(0, feerate=10.0)
        u = UTXO(value=50_000)
        # craft target so this single utxo is an exact changeless match
        c.target = u.effective_value(c.feerate) - c.fixed_fee
        sel = bnb.select_pure([UTXO(value=90_000), u, UTXO(value=12_000)], c)
        assert sel is not None
        r = SelectionResult.build("bnb", c, sel)
        assert r.changeless

    def test_bnb_pure_returns_none_without_match(self):
        c = ctx(30_000, feerate=50.0, ltf=10.0)
        # single huge coin: overshoot way beyond cost_of_change window
        assert bnb.select_pure([UTXO(value=10_000_000)], c) is None

    def test_all_return_none_when_insufficient(self):
        c = ctx(1_000_000)
        utxos = [UTXO(value=10_000)]
        rng = random.Random(0)
        for fn in (largest_first.select, srd.select, knapsack.select, bnb.select):
            assert fn(utxos, c, rng) is None


class TestWaste:
    def test_changeless_at_ltf_equals_excess(self):
        c = ctx(50_000, feerate=10.0, ltf=10.0)
        needed = c.selection_target + round(INPUT_VBYTES * c.feerate)
        r = SelectionResult.build("t", c, [UTXO(value=needed + 100)])
        assert waste(r) == r.excess == 100

    def test_change_waste_is_cost_of_change(self):
        c = ctx(50_000, feerate=10.0, ltf=10.0)
        r = SelectionResult.build("t", c, [UTXO(value=500_000)])
        assert waste(r) == c.cost_of_change

    def test_consolidation_in_low_fees_has_negative_timing_cost(self):
        c = ctx(50_000, feerate=1.0, ltf=10.0)
        r = SelectionResult.build("t", c, [UTXO(value=30_000) for _ in range(5)])
        assert waste(r) < c.cost_of_change  # timing cost is negative