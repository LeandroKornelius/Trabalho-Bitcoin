"""
Largest-first selection.

Greedy baseline: spend the biggest coins first until the target is covered.
Minimizes input count (and thus fees per tx) but almost always creates a
large change output and steadily grinds the wallet's big coins into change.
"""

from __future__ import annotations

import random

from ..models import TxContext, UTXO


def select(utxos: list[UTXO], ctx: TxContext, rng: random.Random | None = None) -> list[UTXO] | None:
    selected: list[UTXO] = []
    total = 0
    for u in sorted(utxos, key=lambda u: u.value, reverse=True):
        ev = u.effective_value(ctx.feerate)
        if ev <= 0:
            continue
        selected.append(u)
        total += ev
        if total >= ctx.selection_target:
            return selected
    return None