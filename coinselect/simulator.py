"""
Scenario simulator.

Replays a sequence of wallet events (receives and payments) against a wallet,
funding each payment with a given coin selection algorithm. Change outputs
return to the wallet, so early selection decisions shape the UTXO pool that
later selections must work with.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .metrics import waste
from .models import SelectionResult, TxContext, UTXO, Wallet

SelectFn = Callable[..., "list[UTXO] | None"]


@dataclass
class Scenario:
    name: str
    long_term_feerate: float
    initial_utxos: list[int]
    events: list[dict]

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        data = json.loads(Path(path).read_text())
        return cls(
            name=data["name"],
            long_term_feerate=data["long_term_feerate"],
            initial_utxos=data["initial_utxos"],
            events=data["events"],
        )


@dataclass
class SimulationRun:
    scenario: str
    algorithm: str
    records: list[dict] = field(default_factory=list)
    failures: int = 0
    final_utxo_count: int = 0
    final_balance: int = 0

    def summary(self) -> dict:
        pays = self.records
        n = len(pays)
        changeless = sum(1 for r in pays if r["changeless"])
        return {
            "scenario": self.scenario,
            "algorithm": self.algorithm,
            "payments": n,
            "failures": self.failures,
            "total_fees": sum(r["fee"] for r in pays),
            "total_waste": sum(r["waste"] for r in pays),
            "mean_inputs": round(sum(r["n_inputs"] for r in pays) / n, 2) if n else 0,
            "changeless_pct": round(100 * changeless / n, 1) if n else 0.0,
            "final_utxo_count": self.final_utxo_count,
            "final_balance": self.final_balance,
        }


def run(scenario: Scenario, algorithm_name: str, select_fn: SelectFn, seed: int = 1234) -> SimulationRun:
    rng = random.Random(seed)
    wallet = Wallet()
    for value in scenario.initial_utxos:
        wallet.receive(value)

    sim = SimulationRun(scenario=scenario.name, algorithm=algorithm_name)
    for i, event in enumerate(scenario.events):
        if event["type"] == "receive":
            wallet.receive(event["amount"])
            continue
        assert event["type"] == "pay", f"unknown event type: {event['type']}"
        ctx = TxContext(
            target=event["amount"],
            feerate=event["feerate"],
            long_term_feerate=scenario.long_term_feerate,
        )
        inputs = select_fn(wallet.utxos, ctx, rng)
        if inputs is None:
            sim.failures += 1
            continue
        result = SelectionResult.build(algorithm_name, ctx, inputs)
        wallet.spend(inputs)
        if result.change > 0:
            wallet.receive(result.change)
        sim.records.append(
            {
                "event": i,
                "target": ctx.target,
                "feerate": ctx.feerate,
                "n_inputs": result.n_inputs,
                "fee": result.fee,
                "change": result.change,
                "changeless": result.changeless,
                "waste": waste(result),
                "utxo_count_after": len(wallet.utxos),
                "balance_after": wallet.balance,
            }
        )

    sim.final_utxo_count = len(wallet.utxos)
    sim.final_balance = wallet.balance
    return sim