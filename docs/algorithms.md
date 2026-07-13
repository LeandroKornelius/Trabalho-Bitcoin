---
layout: default
title: Algorithms
---

# Algorithms

All amounts are satoshis; feerates are sat/vB. We model native segwit (P2WPKH) transactions: **68 vB per input**, **31 vB per output**, **10.5 vB overhead**.

## Effective value and the selection target

Following Erhardt, each UTXO is scored by its **effective value** at the current feerate `f`:

```
effective_value(u) = u.value − 68·f
```

A selection funds a payment of `target` sats when the sum of effective values reaches

```
selection_target = target + (10.5 + 31)·f
```

Meaning that the recipient amount plus the fee are the fixed part of the transaction. Any surplus becomes a change output (paying its own 31·f), unless the resulting change would be dust (≤ 546 sats), in which case the surplus is burned to fees as **excess**.

## Largest-First

- Sort UTXOs by value descending
- Take coins until the target is covered

Then there is a greedy baseline: it minimizes input count and thus per-transaction fees, but almost always produces a large change output and never consolidates small coins. This means that the pool only grows.

## Single Random Draw (SRD)

- Shuffle the pool
- Accumulate until reaching `selection_target + change_fee + 50 000`
- Ffalling back to the bare target when funds are tight

Randomness avoids a deterministic fingerprint and statistically refreshes the pool.

## Knapsack

Simplified form of Bitcoin Core's legacy `ApproximateBestSubset`.

- 1 000 randomized passes accumulating coins toward `target + MIN_CHANGE`, keeping the subset with the smallest overshoot
- Aso onsiders the single smallest UTXO covering the target alone

Aims to minimize the amount tied up in change.

## Branch-and-Bound (BnB)

Erhardt's algorithm.

Depth-first search (largest effective values first, with bounding by remaining sum and a 100 000 node budget) for a **changeless** subset whose effective values land inside


```
[selection_target, selection_target + cost_of_change]
```

where `cost_of_change = 31·f + 68·f_longterm` is the cost of creating change now plus spending it later. When no such subset exists, we fall back to SRD, the same cascade Bitcoin Core uses.

## The waste metric

Scores every candidate selection with

```
waste = timing_cost + creation_cost

timing_cost   = Σ inputs·68·f  −  Σ inputs·68·f_longterm
creation_cost = cost_of_change   (if change is created)
              = excess            (if changeless)
```

Intuitions: 

- spending inputs when `f > f_longterm` is wasteful (you could have waited)
- spending many inputs when `f < f_longterm` is *negative* waste, cheap consolidation
- creating change costs its future spend
- avoiding change costs whatever surplus is burned

Waste was used as the unifying score across all experiments.