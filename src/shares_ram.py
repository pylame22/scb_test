from pathlib import Path

APP_NAME = "shares"


class SharesCalculator:
    def __init__(self, total_sum: float) -> None:
        self._total_sum = total_sum

    def calculate_percentage(self, share: float) -> float:
        return share / self._total_sum


class DataFileIO:
    def __init__(self) -> None:
        self._input_dir = "inputs"
        self._output_dir = "outputs"

    def read_total_sum(self) -> tuple[int, float]:
        total_count = 0
        total_sum = 0.0
        with Path(f"{self._input_dir}/{APP_NAME}.txt").open() as file:
            for idx, line in enumerate(file):
                value = line.strip()
                if not value:
                    continue
                if idx == 0:
                    total_count = int(value)
                else:
                    total_sum += float(value)
        return total_count, total_sum

    def calculate_percentages_streaming(self, calculator: SharesCalculator) -> None:
        path_in = Path(f"{self._input_dir}/{APP_NAME}.txt")
        path_out = Path(f"{self._output_dir}/{APP_NAME}.txt")
        path_out.parent.mkdir(exist_ok=True)

        with path_in.open() as file_in, path_out.open("w") as file_out:
            for idx, line in enumerate(file_in):
                value = line.strip()
                if not value or idx == 0:
                    continue
                percentage = calculator.calculate_percentage(float(value))
                file_out.write(f"{percentage:.3f}\n")


def main() -> None:
    data_file_io = DataFileIO()
    total_count, total_sum = data_file_io.read_total_sum()
    if total_count <= 0:
        msg = f"Invalid total_count value: {total_count}"
        raise ValueError(msg)
    calculator = SharesCalculator(total_sum)
    data_file_io.calculate_percentages_streaming(calculator)


if __name__ == "__main__":
    main()
