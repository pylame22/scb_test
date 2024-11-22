import logging
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "trader"


@dataclass(slots=True)
class LotSchema:
    day_number: int
    name: str
    price_percent: float
    size: int


@dataclass(slots=True)
class TraderSchema:
    total_days: int
    lot_count_per_day: int
    total_funds: int
    lots: list[LotSchema] = field(default_factory=list)

    def validate(self) -> None:
        day_numbers = [lot.day_number for lot in self.lots]
        max_lot_count_per_day = max(Counter(day_numbers).values())
        max_total_days = max(day_numbers)

        if self.total_days != max_total_days:
            msg = f"invalid total_days value {self.total_days}"
            raise ValueError(msg)
        if self.lot_count_per_day != max_lot_count_per_day:
            msg = f"invalid lot_count_per_day value {self.lot_count_per_day}"
            raise ValueError(msg)


@dataclass(slots=True)
class LotsResultSchema:
    lots: tuple[int, ...] = field(default_factory=tuple)
    profit: int = 0
    cost: int = 0


class BaseTrader(ABC):
    def __init__(
        self,
        trader_schema: TraderSchema,
        *,
        bond_redemtion_days: int,
        bond_par_value: int,
        bond_payment_per_day: int,
    ) -> None:
        self._total_days = trader_schema.total_days
        self._total_funds = trader_schema.total_funds
        self._lots = trader_schema.lots
        self._bond_redemtion_days = bond_redemtion_days
        self._bond_par_value = bond_par_value
        self._bond_payment_per_day = bond_payment_per_day
        self._days_factor = self._total_days + self._bond_redemtion_days

    def _calculate_profit(self, lot: LotSchema) -> tuple[int, int]:
        lot_price = int(lot.price_percent * self._bond_par_value // 100)
        bond_profit = (self._days_factor - lot.day_number) * self._bond_payment_per_day
        bond_consumption = self._bond_par_value - lot_price
        lot_profit = lot.size * (bond_profit + bond_consumption)
        lot_cost = lot.size * lot_price
        return lot_profit, lot_cost

    @classmethod
    @abstractmethod
    def get_complexity(cls, trader_schema: TraderSchema) -> int:
        pass

    @abstractmethod
    def calculate(self) -> LotsResultSchema:
        pass


class TraderSubset(BaseTrader):
    @classmethod
    def get_complexity(cls, trader_schema: TraderSchema) -> int:
        lots_count = len(trader_schema.lots)
        return lots_count * (2**lots_count)

    def calculate(self) -> LotsResultSchema:
        result = LotsResultSchema()
        lots_map: dict[tuple[int, ...], tuple[int, int]] = {(): (0, 0)}
        for idx, lot in enumerate(self._lots):
            lot_profit, lot_cost = self._calculate_profit(lot)
            new_lots_map = lots_map.copy()
            for used_lots, (profit, cost) in lots_map.items():
                new_profit = profit + lot_profit
                new_cost = lot_cost + cost
                if new_cost <= self._total_funds:
                    new_lots = (*used_lots, idx)
                    new_lots_map[new_lots] = (new_profit, new_cost)
                    if new_profit > result.profit:
                        result.lots = new_lots
                        result.profit = new_profit
                        result.cost = new_cost
            lots_map = new_lots_map
        return result


class TraderDP(BaseTrader):
    @classmethod
    def get_complexity(cls, trader_schema: TraderSchema) -> int:
        return len(trader_schema.lots) * trader_schema.total_funds

    def calculate(self) -> LotsResultSchema:
        max_profit = [0] * (self._total_funds + 1)
        lot_choices: list[list[int]] = [[] for _ in range(self._total_funds + 1)]
        for idx, lot in enumerate(self._lots):
            lot_profit, lot_cost = self._calculate_profit(lot)
            for funds in range(self._total_funds, lot_cost - 1, -1):
                new_profit = max_profit[funds - lot_cost] + lot_profit
                if new_profit > max_profit[funds]:
                    max_profit[funds] = new_profit
                    lot_choices[funds] = lot_choices[funds - lot_cost] + [idx]
        max_funds = max(range(self._total_funds + 1), key=lambda x: max_profit[x])
        return LotsResultSchema(
            lots=tuple(lot_choices[max_funds]),
            profit=max_profit[max_funds],
            cost=max_funds,
        )


class DataFileIO:
    def __init__(self) -> None:
        self._input_dir = "inputs"
        self._output_dir = "outputs"

    def read_input(self) -> TraderSchema:
        trader_schema: TraderSchema | None = None
        with Path(f"{self._input_dir}/{APP_NAME}.txt").open() as file:
            for line in file:
                if not line.strip():
                    continue
                values = line.split()
                if trader_schema:
                    trader_schema.lots.append(
                        LotSchema(
                            day_number=int(values[0]),
                            name=values[1],
                            price_percent=float(values[2]),
                            size=int(values[3]),
                        ),
                    )
                else:
                    trader_schema = TraderSchema(
                        total_days=int(values[0]),
                        lot_count_per_day=int(values[1]),
                        total_funds=int(values[2]),
                    )
        if not trader_schema:
            msg = f"input file invalid, check inputs/{APP_NAME}.txt"
            raise ValueError(msg)
        return trader_schema

    def write_output(self, profit: int, lots: list[LotSchema]) -> None:
        path = Path(f"{self._output_dir}/{APP_NAME}.txt")
        path.parent.mkdir(exist_ok=True)
        with path.open("w") as file:
            file.write(f"{profit}\n")
            for lot in lots:
                file.write(f"{lot.day_number} {lot.name} {lot.price_percent} {lot.size}\n")


def _get_trader_class(trader_schema: TraderSchema) -> type[BaseTrader]:
    trader_classes: tuple[type[BaseTrader], ...] = (
        TraderSubset,
        TraderDP,
    )
    return min(trader_classes, key=lambda strategy: strategy.get_complexity(trader_schema))


def main() -> None:
    logger = logging.getLogger(APP_NAME)
    logging.basicConfig(level=logging.INFO)

    data_file_io = DataFileIO()
    trader_schema = data_file_io.read_input()
    trader_schema.validate()

    trader_class = _get_trader_class(trader_schema)
    logger.info("selected class: %s", trader_class.__name__)
    trader = trader_class(trader_schema, bond_redemtion_days=30, bond_par_value=1000, bond_payment_per_day=1)
    result = trader.calculate()
    logger.info("result: %s", result)

    result_lots = [trader_schema.lots[lot_idx] for lot_idx in sorted(result.lots)]
    data_file_io.write_output(result.profit, result_lots)


if __name__ == "__main__":
    main()
