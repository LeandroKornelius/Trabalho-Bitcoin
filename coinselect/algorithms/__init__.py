"""
Coin selection algorithms.
"""

from . import bnb, knapsack, largest_first, srd

ALGORITHMS = {
    "largest_first": largest_first.select,
    "srd": srd.select,
    "knapsack": knapsack.select,
    "bnb": bnb.select,  # SRD fallback
}