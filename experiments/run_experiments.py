"""
Run every algorithm against every scenario and produce the artifacts
used by the article: results/summary.csv + figures in docs/assets/.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coinselect.algorithms import ALGORITHMS  # noqa: E402
from coinselect.simulator import Scenario, run  # noqa: E402

RESULTS = ROOT / "results"
ASSETS = ROOT / "docs" / "assets"
SEED = 1234

COLORS = {
    "largest_first": "#d62728",
    "srd": "#1f77b4",
    "knapsack": "#ff7f0e",
    "bnb": "#2ca02c",
}
LABELS = {
    "largest_first": "Largest-First",
    "srd": "SRD",
    "knapsack": "Knapsack",
    "bnb": "BnB (+SRD)",
}


def grouped_bar(summaries, key, title, ylabel, filename, scale=1.0):
    scenarios = sorted({s["scenario"] for s in summaries})
    algos = list(ALGORITHMS)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.8 / len(algos)
    for j, algo in enumerate(algos):
        xs = [i + j * width for i in range(len(scenarios))]
        ys = [
            next(s[key] for s in summaries if s["scenario"] == sc and s["algorithm"] == algo) * scale
            for sc in scenarios
        ]
        ax.bar(xs, ys, width=width, label=LABELS[algo], color=COLORS[algo])
    ax.set_xticks([i + 0.4 - width / 2 for i in range(len(scenarios))])
    ax.set_xticklabels(scenarios)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(ASSETS / filename, dpi=150)
    plt.close(fig)


def utxo_timeline(runs_by_algo, scenario_name):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for algo, sim in runs_by_algo.items():
        xs = [r["event"] for r in sim.records]
        ys = [r["utxo_count_after"] for r in sim.records]
        ax.plot(xs, ys, label=LABELS[algo], color=COLORS[algo], linewidth=1.6)
    ax.set_title(f"UTXO pool size over time — {scenario_name}")
    ax.set_xlabel("event index")
    ax.set_ylabel("# UTXOs in wallet")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ASSETS / f"utxos_{scenario_name}.png", dpi=150)
    plt.close(fig)


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    scenario_paths = sorted((ROOT / "scenarios").glob("*.json"))
    if not scenario_paths:
        sys.exit("No scenarios found — run: python scenarios/generate.py")

    summaries = []
    for path in scenario_paths:
        scenario = Scenario.load(path)
        runs_by_algo = {}
        for algo_name, fn in ALGORITHMS.items():
            sim = run(scenario, algo_name, fn, seed=SEED)
            runs_by_algo[algo_name] = sim
            summaries.append(sim.summary())
        utxo_timeline(runs_by_algo, scenario.name)

    with open(RESULTS / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    grouped_bar(summaries, "total_fees", "Total fees paid", "sats", "fees.png")
    grouped_bar(summaries, "total_waste", "Total waste (Bitcoin Core metric)", "sats", "waste.png")
    grouped_bar(summaries, "changeless_pct", "Changeless transactions", "% of payments", "changeless.png")
    grouped_bar(summaries, "final_utxo_count", "Final UTXO pool size", "# UTXOs", "final_utxos.png")

    # console report
    cols = list(summaries[0])
    print(" | ".join(cols))
    for s in summaries:
        print(" | ".join(str(s[c]) for c in cols))
    print(f"\nwrote {RESULTS / 'summary.csv'} and figures to {ASSETS}/")


if __name__ == "__main__":
    main()