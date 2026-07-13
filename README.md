# Coin Selection Lab

## Alunos: Leandro Beloti Kornelius & Vítor Caldas Danelon 

Simulating and comparing Bitcoin coin selection algorithms

## [Vídeo de Apresentação](https://youtu.be/E2LcucONhsk)

## What it does

Implements four coin selection algorithms: Largest-First, Single Random Draw,
Knapsack and Branch-and-Bound (with SRD fallback) and
replays them over deterministic wallet-lifetime scenarios (retail, hodler,
merchant). Compares total fees, Bitcoin Core's *waste* metric, changeless
transaction rate and UTXO pool fragmentation over time.

## Layout

```
coinselect/            library: models, metrics, simulator
coinselect/algorithms/ largest_first, srd, knapsack, bnb
scenarios/             deterministic scenario JSONs + generator
experiments/           experiment runner (generates CSV + figures)
results/               summary.csv
docs/                  article
tests/                 unit tests
```

## Running

```bash
pip install -r requirements.txt
python -m pytest tests/                  # 14 tests
python scenarios/generate.py             # regenerate scenarios (seeded)
python experiments/run_experiments.py    # writes results/ and docs/assets/
```ß