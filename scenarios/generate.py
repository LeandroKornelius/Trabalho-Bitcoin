"""
Deterministically generate the simulation scenarios (seed fixed).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

OUT_DIR = Path(__file__).parent


def feerate(rng: random.Random) -> float:
    """Fee regime: mostly calm, sometimes busy, occasionally a spike."""
    roll = rng.random()
    if roll < 0.60:
        return round(rng.uniform(1, 10), 1)      # calm mempool
    if roll < 0.90:
        return round(rng.uniform(10, 40), 1)     # busy
    return round(rng.uniform(40, 150), 1)        # fee spike


def retail(rng: random.Random) -> dict:
    """Personal wallet: frequent small receives and payments."""
    events = []
    for _ in range(160):
        if rng.random() < 0.55:
            events.append({"type": "receive", "amount": rng.randint(5_000, 150_000)})
        else:
            events.append(
                {"type": "pay", "amount": rng.randint(2_000, 80_000), "feerate": feerate(rng)}
            )
    return {
        "name": "retail",
        "long_term_feerate": 10.0,
        "initial_utxos": [30_000, 30_000, 30_000, 100_000],
        "events": events,
    }


def hodler(rng: random.Random) -> dict:
    """Saver: few large receives, rare payments."""
    events = []
    for _ in range(30):
        if rng.random() < 0.6:
            events.append({"type": "receive", "amount": rng.randint(1_000_000, 10_000_000)})
        else:
            events.append(
                {"type": "pay", "amount": rng.randint(200_000, 2_000_000), "feerate": feerate(rng)}
            )
    return {
        "name": "hodler",
        "long_term_feerate": 10.0,
        "initial_utxos": [5_000_000],
        "events": events,
    }


def merchant(rng: random.Random) -> dict:
    """Merchant: heavy inflow of medium payments, periodic large payouts."""
    events = []
    for _ in range(400):
        if rng.random() < 0.75:
            events.append({"type": "receive", "amount": rng.randint(10_000, 400_000)})
        else:
            events.append(
                {"type": "pay", "amount": rng.randint(100_000, 600_000), "feerate": feerate(rng)}
            )
    return {
        "name": "merchant",
        "long_term_feerate": 10.0,
        "initial_utxos": [50_000] * 10,
        "events": events,
    }


def main() -> None:
    rng = random.Random(42)
    for build in (retail, hodler, merchant):
        scenario = build(rng)
        path = OUT_DIR / f"{scenario['name']}.json"
        path.write_text(json.dumps(scenario, indent=1))
        pays = sum(1 for e in scenario["events"] if e["type"] == "pay")
        print(f"wrote {path.name}: {len(scenario['events'])} events ({pays} payments)")


if __name__ == "__main__":
    main()