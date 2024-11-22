from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "shares"


@dataclass(slots=True)
class SharesSchema:
    total_count: int
    total_sum: float = 0.0
    data: list[float] = field(default_factory=list)

    def validate(self) -> None:
        if self.total_count != len(self.data):
            msg = f"invalid total_count value {self.total_count}"
            raise ValueError(msg)


class SharesCalculator:
    def __init__(self, shares_schema: SharesSchema) -> None:
        self._shares = shares_schema.data
        self._shares_sum = shares_schema.total_sum

    def calculate(self) -> list[float]:
        return [share / self._shares_sum for share in self._shares]


class DataFileIO:
    def __init__(self) -> None:
        self._input_dir = "inputs"
        self._output_dir = "outputs"

    def read_input(self) -> SharesSchema:
        shares_schema: SharesSchema | None = None
        with Path(f"{self._input_dir}/{APP_NAME}.txt").open() as file:
            for line in file:
                if not line.strip():
                    continue
                if shares_schema:
                    shares_schema.total_sum += float(line)
                    shares_schema.data.append(float(line))
                else:
                    shares_schema = SharesSchema(total_count=int(line))
        if not shares_schema:
            msg = f"input file invalid, check inputs/{APP_NAME}.txt"
            raise ValueError(msg)
        return shares_schema

    def write_output(self, percentages: list[float]) -> None:
        path = Path(f"{self._output_dir}/{APP_NAME}.txt")
        path.parent.mkdir(exist_ok=True)
        with path.open("w") as file:
            for percentage in percentages:
                file.write(f"{percentage:.3f}\n")


def main() -> None:
    data_file_io = DataFileIO()
    shares_schema = data_file_io.read_input()
    shares_schema.validate()

    calulator = SharesCalculator(shares_schema)
    result = calulator.calculate()
    data_file_io.write_output(result)


if __name__ == "__main__":
    main()
