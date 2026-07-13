"""
Branch-and-Bound (BnB), Erhardt 2016 / Bitcoin Core.

Searches for a *changeless* solution: a subset of UTXOs whose effective
values sum to within [target, target + cost_of_change]. Avoiding change
saves the cost of creating and later spending a change output, and improves
privacy (no change output to fingerprint).

Pure BnB fails whenever no exact-ish match exists, so — like Bitcoin Core —
`select` falls back to Single Random Draw. `select_pure` exposes the raw
search for tests and analysis.
"""

from __future__ import annotations

import random

from ..models import TxContext, UTXO
from . import srd

MAX_TRIES = 100_000


def select_pure(utxos: list[UTXO], ctx: TxContext, max_tries: int = MAX_TRIES) -> list[UTXO] | None:
    target = ctx.selection_target
    upper = target + ctx.cost_of_change
    pool = [(u, u.effective_value(ctx.feerate)) for u in utxos]
    pool = [(u, ev) for u, ev in pool if ev > 0]
    pool.sort(key=lambda t: t[1], reverse=True)
    if sum(ev for _, ev in pool) < target:
        return None

    # suffix[i] = sum of effective values from i to the end
    suffix = [0] * (len(pool) + 1)
    for i in range(len(pool) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + pool[i][1]

    tries = 0

    def dfs(i: int, current: int, chosen: list[UTXO]) -> list[UTXO] | None:
        nonlocal tries
        tries += 1
        if current > upper:
            return None
        if current >= target:
            return list(chosen)
        if tries >= max_tries or i == len(pool):
            return None
        if current + suffix[i] < target:
            return None
        # Branch 1: include pool[i]
        chosen.append(pool[i][0])
        found = dfs(i + 1, current + pool[i][1], chosen)
        if found is not None:
            return found
        chosen.pop()
        # Branch 2: exclude pool[i]
        return dfs(i + 1, current, chosen)

    return dfs(0, 0, [])


def select(utxos: list[UTXO], ctx: TxContext, rng: random.Random | None = None) -> list[UTXO] | None:
    """BnB with SRD fallback (mirrors Bitcoin Core's solver cascade)."""
    result = select_pure(utxos, ctx)
    if result is not None:
        return result
    return srd.select(utxos, ctx, rng)