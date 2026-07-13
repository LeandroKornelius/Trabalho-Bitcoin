"""
Coin Selection Lab: simulate and compare Bitcoin coin selection algorithms.
"""

from .algorithms import ALGORITHMS
from .metrics import waste
from .models import DUST_THRESHOLD, SelectionResult, TxContext, UTXO, Wallet

__all__ = [
    "ALGORITHMS",
    "DUST_THRESHOLD",
    "SelectionResult",
    "TxContext",
    "UTXO",
    "Wallet",
    "waste",
]