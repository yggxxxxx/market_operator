from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class TariffProfile:
    tariff_name: str
    target_year: int
    hourly_prices_gbp_per_kwh: dict

    def get_price(self, hour):
        if not isinstance(hour, int):
            raise TypeError(f"hour must be int, got {type(hour).__name__}")

        if hour < 0 or hour > 23:
            raise ValueError(f"hour must be between 0 and 23, got {hour}")

        return self.hourly_prices_gbp_per_kwh[hour]

    def to_dataframe(self):
        rows = []
        for hour in range(24):
            rows.append({
                "hour": hour,
                "price_gbp_per_kwh": self.hourly_prices_gbp_per_kwh[hour]
            })
        return pd.DataFrame(rows)


class TariffLoader:
    COLUMN_NAMES = [
        "timestamp",
        "time_label",
        "region_code",
        "region_name",
        "price_pence_per_kwh",
    ]

    def load_raw_tariff_csv(self, csv_path):
        csv_path = Path(csv_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"Tariff CSV not found: {csv_path}")

        df = pd.read_csv(csv_path, header=None, names=self.COLUMN_NAMES)

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        df["price_pence_per_kwh"] = pd.to_numeric(
            df["price_pence_per_kwh"],
            errors="coerce"
        )

        df = df.dropna(subset=["timestamp", "price_pence_per_kwh"]).copy()
        df["price_gbp_per_kwh"] = df["price_pence_per_kwh"] / 100.0

        return df

    def build_representative_day_profile(self, csv_path, tariff_name, target_year=2026):
        df = self.load_raw_tariff_csv(csv_path)

        df_year = df[df["timestamp"].dt.year == target_year].copy()

        if df_year.empty:
            raise ValueError(
                f"No tariff data found for year {target_year} in file: {csv_path}"
            )

        df_year["hour"] = df_year["timestamp"].dt.hour

        hourly_avg = (
            df_year.groupby("hour")["price_gbp_per_kwh"]
            .mean()
            .reindex(range(24))
        )

        if hourly_avg.isna().any():
            missing_hours = hourly_avg[hourly_avg.isna()].index.tolist()
            raise ValueError(
                f"Missing tariff data for hours {missing_hours} in year {target_year}"
            )

        hourly_prices_gbp_per_kwh = {}
        for hour, price in hourly_avg.items():
            hourly_prices_gbp_per_kwh[int(hour)] = float(price)

        return TariffProfile(
            tariff_name=tariff_name,
            target_year=target_year,
            hourly_prices_gbp_per_kwh=hourly_prices_gbp_per_kwh
        )


def load_tou_profile(csv_path="csv_agile_L_South_Western_England.csv", target_year=2026):
    loader = TariffLoader()
    return loader.build_representative_day_profile(
        csv_path=csv_path,
        tariff_name="ToU",
        target_year=target_year
    )


def load_fit_profile(csv_path="csv_agileoutgoing_L_South_Western_England.csv", target_year=2026):
    loader = TariffLoader()
    return loader.build_representative_day_profile(
        csv_path=csv_path,
        tariff_name="FiT",
        target_year=target_year
    )