"""
Knapsack (stochastic approximation).

Simplified version of Bitcoin Core's legacy solver (ApproximateBestSubset):
run many randomized passes accumulating coins until the target is reached and
keep the smallest-overshoot subset found. Also considers the single smallest
UTXO that covers the target on its own ("lowest larger"), as Core does.

Like Core, it aims for target + MIN_CHANGE to avoid producing dust change,
falling back to the bare target when funds are tight.
"""

from __future__ import annotations

import random

from ..models import TxContext, UTXO

MIN_CHANGE = 50_000  # sats


def select(
    utxos: list[UTXO],
    ctx: TxContext,
    rng: random.Random | None = None,
    iterations: int = 1000,
) -> list[UTXO] | None:
    rng = rng or random.Random()
    pool = [(u, u.effective_value(ctx.feerate)) for u in utxos]
    pool = [(u, ev) for u, ev in pool if ev > 0]
    total_available = sum(ev for _, ev in pool)
    base = ctx.selection_target
    if total_available < base:
        return None
    target = base + MIN_CHANGE if total_available >= base + MIN_CHANGE else base

    # Single smallest UTXO that covers the target alone.
    singles = [(u, ev) for u, ev in pool if ev >= target]
    best_single = min(singles, key=lambda t: t[1]) if singles else None

    best_set: list[UTXO] | None = None
    best_total: int | None = None
    for _ in range(iterations):
        order = pool[:]
        rng.shuffle(order)
        chosen: list[UTXO] = []
        total = 0
        for u, ev in order:
            chosen.append(u)
            total += ev
            if total >= target:
                break
        if total >= target and (best_total is None or total < best_total):
            best_set, best_total = chosen, total
            if total == target:
                break

    if best_single is not None and (best_total is None or best_single[1] < best_total):
        return [best_single[0]]
    return best_set