from dataclasses import dataclass
import random
import pandas as pd


@dataclass
class TestHouseholdResult:
    h_id: int
    demand: float
    pv: float
    battery_charged: float
    battery_discharged: float
    energy_before: float
    energy_after: float
    import_energy: float
    export_energy: float
    soc: float
    DateTime: str


def generate_one_test_household_result(h_id: int, DateTime: str) -> TestHouseholdResult:
    """
    Generate one random household result using the same variable names
    as the existing household code style.
    """
    demand = round(random.uniform(1, 20), 3)
    pv = round(random.uniform(1, 20), 3)
    soc = round(random.uniform(0.2, 0.95), 3)

    energy_before = round(demand - pv, 3)

    battery_charged = 0.0
    battery_discharged = 0.0

    # mimic the same style as agent.py:
    # if deficit -> maybe discharge battery
    # if surplus -> maybe charge battery
    if energy_before > 0:
        battery_discharged = round(random.uniform(0.0, min(energy_before, 2.5)), 3)
    elif energy_before < 0:
        surplus = abs(energy_before)
        battery_charged = round(random.uniform(0.0, min(surplus, 2.5)), 3)

    energy_after = round(
        demand - pv - battery_discharged + battery_charged,
        3
    )

    import_energy = round(max(0.0, energy_after), 3)
    export_energy = round(max(0.0, -energy_after), 3)

    return TestHouseholdResult(
        h_id=h_id,
        demand=demand,
        pv=pv,
        battery_charged=battery_charged,
        battery_discharged=battery_discharged,
        energy_before=energy_before,
        energy_after=energy_after,
        import_energy=import_energy,
        export_energy=export_energy,
        soc=soc,
        DateTime=DateTime,
    )


def generate_test_households(
    num_households: int = 20,
    DateTime: str = "2026-01-01 18:00:00"
) -> pd.DataFrame:
    """
    Generate random household results for market testing.

    Output column names follow the same style as the existing household code.
    """
    results = []

    for h_id in range(1, num_households + 1):
        result = generate_one_test_household_result(
            h_id=h_id,
            DateTime=DateTime
        )
        results.append(result.__dict__)

    return pd.DataFrame(results)


if __name__ == "__main__":
    random.seed(42)

    test_df = generate_test_households(num_households=20)

    pd.set_option("display.max_rows", None)
    print(test_df[[
        "DateTime",
        "h_id",
        "demand",
        "pv",
        "battery_charged",
        "battery_discharged",
        "energy_before",
        "energy_after",
        "import_energy",
        "export_energy",
        "soc"
    ]])