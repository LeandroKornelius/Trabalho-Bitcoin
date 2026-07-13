"""
Single Random Draw (SRD).

Bitcoin Core's simplest solver: shuffle the UTXO pool and accumulate coins
until the target is reached. Core aims for target + CHANGE_LOWER so the
change output is always economically useful; we do the same with MIN_CHANGE,
falling back to the bare target when the wallet is too small for that.

Randomness gives SRD a privacy benefit (no deterministic fingerprint) and,
on average, keeps the UTXO pool healthy.
"""

from __future__ import annotations

import random

from ..models import TxContext, UTXO

MIN_CHANGE = 50_000  # sats; Core's CHANGE_LOWER


def select(utxos: list[UTXO], ctx: TxContext, rng: random.Random | None = None) -> list[UTXO] | None:
    rng = rng or random.Random()
    pool = [u for u in utxos if u.effective_value(ctx.feerate) > 0]
    total_available = sum(u.effective_value(ctx.feerate) for u in pool)
    if total_available < ctx.selection_target:
        return None
    target = ctx.selection_target + ctx.change_output_fee + MIN_CHANGE
    if total_available < target:
        target = ctx.selection_target
    rng.shuffle(pool)
    selected: list[UTXO] = []
    total = 0
    for u in pool:
        selected.append(u)
        total += u.effective_value(ctx.feerate)
        if total >= target:
            return selected
    return None