---
layout: default
title: Coin Selection Lab
---

# Coin Selection Lab

## Alunos: Leandro Beloti Kornelius & Vítor Caldas Danelon 

## [Vídeo de Apresentação](https://youtu.be/E2LcucONhsk)

**Simulating and comparing Bitcoin coin selection algorithms**

Final project for "Tópicos Avançados em Computadores" (CIC0087), class of the University of Brasilia (UnB).  

---

## The problem

Every time a Bitcoin wallet sends a payment, it must answer a deceptively simple question: *which of my UTXOs should fund this transaction?* This is **coin selection**, and the answer affects three things at once:

1. **Fees.** Each input adds ~68 vB to the transaction, so spending many small coins during a fee spike is expensive.
2. **Privacy.** Most selections produce a *change output* that returns to the wallet. Change is the main hook for chain-analysis heuristics: it links future spends back to past ones.
3. **Wallet health.** Change outputs feed back into the UTXO pool. A wallet that always spends its largest coin slowly grinds its balance into fragments that may become uneconomical to spend ("dust") when fees rise.

The three goals conflict. Minimizing fees *today* (fewest inputs) maximizes fragmentation *tomorrow*; avoiding change helps privacy but is only possible when the pool happens to contain a matching subset. Bitcoin Core acknowledges this tension with its **waste metric**, a single score that prices both the timing of input spending and the cost of change.

## Why it matters to the ecosystem

Coin selection is one of the few consensus-independent components where wallet engineering directly shapes user costs and on-chain privacy for millions of users. Bitcoin Core alone ships three solvers (Branch-and-Bound, knapsack, Single Random Draw) and chooses among them per transaction. Yet the trade-offs between them are rarely quantified outside of Erhardt's simulation work, most wallets pick an algorithm once and never measure the long-term effect on their users' UTXO pools.

## Our solution

We built the **Coin Selection Lab**: a small, tested Python framework that

- implements four selection algorithms — **Largest-First**, **Single Random Draw (SRD)**, **Knapsack** and **Branch-and-Bound (BnB, with SRD fallback, mirroring Bitcoin Core's cascade)** — over a realistic P2WPKH fee model with effective values, dust handling and Core's waste metric;
- replays deterministic **wallet-lifetime scenarios** (a retail user, a hodler, a merchant. Hundreds of receives/payments under varying fee regimes), where each algorithm's change outputs feed back into its own future selections;
- measures **total fees, waste, changeless-transaction rate and UTXO pool size over time**, producing the figures and tables in [Results](results.html).

**Headline result:** in the merchant scenario, BnB made **68.9% of payments without any change output** and cut total waste by **37% vs. SRD**, while paying fees within 3% of the greedy fee-minimizing baseline. However, Largest-First, despite the lowest fees per transaction, left the wallet with **229 UTXOs (2× more than any other algorithm)**, a fragmentation debt that comes due in the next fee spike.

## Documentation

- **[Algorithms](algorithms.html)**: formal description of each strategy and of the waste metric.
- **[Results](results.html)**: experimental setup, figures and discussion.
- **[Reference](https://arxiv.org/pdf/2311.01113)**: coin selection algorithms and their caracteristics.