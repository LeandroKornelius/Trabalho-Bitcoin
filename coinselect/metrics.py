"""
Metrics for evaluating coin selections.
"""

from __future__ import annotations

from .models import INPUT_VBYTES, SelectionResult


def waste(result: SelectionResult) -> int:
    ctx = result.ctx
    fee_now = sum(u.input_fee(ctx.feerate) for u in result.inputs)
    fee_long_term = result.n_inputs * round(INPUT_VBYTES * ctx.long_term_feerate)
    timing_cost = fee_now - fee_long_term
    creation_cost = result.excess if result.changeless else ctx.cost_of_change
    return timing_cost + creation_cost