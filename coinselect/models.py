"""
Core data models for the Coin Selection Lab.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

# Typical vbyte sizes for a P2WPKH transaction.
INPUT_VBYTES = 68.0
OUTPUT_VBYTES = 31.0
TX_OVERHEAD_VBYTES = 10.5

# Outputs below this are considered dust and are dropped to fees.
DUST_THRESHOLD = 546

_uid_counter = itertools.count()


@dataclass(frozen=True)
class UTXO:
    """An unspent transaction output owned by the wallet."""

    value: int
    uid: int = field(default_factory=lambda: next(_uid_counter))

    def input_fee(self, feerate: float) -> int:
        """Fee to spend this UTXO as an input at the given feerate."""
        return round(INPUT_VBYTES * feerate)

    def effective_value(self, feerate: float) -> int:
        """Value net of the cost of spending it (Erhardt's effective value)."""
        return self.value - self.input_fee(feerate)


@dataclass
class TxContext:
    """Parameters of the payment the wallet needs to fund."""

    target: int                     # amount going to the recipient
    feerate: float                  # current feerate
    long_term_feerate: float = 10.0  # expected long-term feerate

    @property
    def fixed_fee(self) -> int:
        """Fee for tx overhead + the recipient output, regardless of inputs"""
        return round((TX_OVERHEAD_VBYTES + OUTPUT_VBYTES) * self.feerate)

    @property
    def selection_target(self) -> int:
        """Sum of effective values a selection must reach to fund the tx."""
        return self.target + self.fixed_fee

    @property
    def change_output_fee(self) -> int:
        """Cost of adding a change output to this transaction."""
        return round(OUTPUT_VBYTES * self.feerate)

    @property
    def cost_of_change(self) -> int:
        """Cost of creating change now plus spending it later at the
        long-term feerate"""
        return self.change_output_fee + round(INPUT_VBYTES * self.long_term_feerate)


@dataclass
class SelectionResult:
    """A funded transaction: chosen inputs plus derived change/fee."""

    algorithm: str
    ctx: TxContext
    inputs: list[UTXO]
    change: int = 0
    excess: int = 0  # surplus burned to fees when no change is created
    fee: int = 0

    @classmethod
    def build(cls, algorithm: str, ctx: TxContext, inputs: list[UTXO]) -> "SelectionResult":
        eff_sum = sum(u.effective_value(ctx.feerate) for u in inputs)
        surplus = eff_sum - ctx.selection_target
        if surplus < 0:
            raise ValueError("selection does not fund the transaction")
        change_value = surplus - ctx.change_output_fee
        if change_value > DUST_THRESHOLD:
            change, excess = change_value, 0
        else:
            change, excess = 0, surplus
        total_in = sum(u.value for u in inputs)
        fee = total_in - ctx.target - change
        return cls(algorithm, ctx, list(inputs), change, excess, fee)

    @property
    def n_inputs(self) -> int:
        return len(self.inputs)

    @property
    def changeless(self) -> bool:
        return self.change == 0


@dataclass
class Wallet:
    """A minimal UTXO-based wallet."""

    utxos: list[UTXO] = field(default_factory=list)

    def receive(self, value: int) -> UTXO:
        utxo = UTXO(value=value)
        self.utxos.append(utxo)
        return utxo

    def spend(self, inputs: list[UTXO]) -> None:
        spent = {u.uid for u in inputs}
        self.utxos = [u for u in self.utxos if u.uid not in spent]

    @property
    def balance(self) -> int:
        return sum(u.value for u in self.utxos)