from dataclasses import dataclass
import random


@dataclass
class MarketSignal:
    reference_price_gbp_per_kwh: float
    accepted: bool
    last_shout_type: str    # "bid" or "ask"


def limited_margin(value, lower=0.0, upper=0.5):
    return max(lower, min(value, upper))


def limited_price(price, fit_price_gbp_per_kwh, tou_price_gbp_per_kwh):
    return max(fit_price_gbp_per_kwh, min(price, tou_price_gbp_per_kwh))


def generate_price(trader):
    if trader.fit_price_gbp_per_kwh is None:
        raise ValueError("fit_price_gbp_per_kwh cannot define")

    if trader.tou_price_gbp_per_kwh is None:
        raise ValueError("tou_price_gbp_per_kwh cannot define")

    if trader.side == "sell":
        price = trader.fit_price_gbp_per_kwh * (1 + trader.margin)

    elif trader.side == "buy":
        price = trader.tou_price_gbp_per_kwh * (1 - trader.margin)

    else:
        raise ValueError("Cannot identify the buyer or seller")

    price = limited_price(
        price,
        trader.fit_price_gbp_per_kwh,
        trader.tou_price_gbp_per_kwh
    )
    return price


def determine_zip_action(trader, q, accepted, last_shout_type):
    if last_shout_type not in {"bid", "ask"}:
        raise ValueError("Cannot identify the last_shout_type 'bid' or 'ask'")

    p_i = generate_price(trader)

    if trader.side == "sell":
        if accepted:
            if p_i <= q:
                return "raise"
            if last_shout_type == "bid" and p_i >= q:
                return "lower"
            return "none"
        else:
            if last_shout_type == "ask" and p_i >= q:
                return "lower"
            return "none"

    elif trader.side == "buy":
        if accepted:
            if p_i >= q:
                return "raise"
            if last_shout_type == "ask" and p_i <= q:
                return "lower"
            return "none"
        else:
            if last_shout_type == "bid" and p_i <= q:
                return "lower"
            return "none"

    else:
        raise ValueError("Cannot identify the buyer or seller")


def update_margin_direct(trader, action, step_size=0.02):
    if action not in {"raise", "lower", "none"}:
        raise ValueError("Cannot identify the action 'raise', 'lower', or 'none'")

    if action == "none":
        trader.last_margin_adjustment = 0.0
        return

    direction = 1.0 if action == "raise" else -1.0

    raw_adjustment = direction * trader.beta * step_size
    new_adjustment = (trader.gamma * trader.last_margin_adjustment + (1.0 - trader.gamma) * raw_adjustment)

    trader.margin = limited_margin(trader.margin + new_adjustment, 0.0, 0.5)
    trader.last_margin_adjustment = new_adjustment


def update_zip(trader, signal: MarketSignal, step_size=0.02):
    q = signal.reference_price_gbp_per_kwh

    action = determine_zip_action(
        trader=trader,
        q=q,
        accepted=signal.accepted,
        last_shout_type=signal.last_shout_type
    )

    update_margin_direct(trader, action, step_size=step_size)
    return action


class ZIPStrategy:
    def __init__(self, h_id: int, side: str):
        if side not in {"buy", "sell"}:
            raise ValueError("Cannot identify the buyer or seller")

        self.h_id = h_id
        self.household_id = h_id
        self.side = side

        self.beta = random.uniform(0.1, 0.5)
        self.gamma = random.uniform(0.0, 0.1)
        self.margin = random.uniform(0.05, 0.35)

        self.last_margin_adjustment = 0.0

        self.fit_price_gbp_per_kwh = None
        self.tou_price_gbp_per_kwh = None
        self.remaining_quantity = 0.0

    def generate_shout(self, fit_price_gbp_per_kwh: float, tou_price_gbp_per_kwh: float) -> float:
        if fit_price_gbp_per_kwh <= 0:
            raise ValueError("fit_price_gbp_per_kwh must be > 0")

        if tou_price_gbp_per_kwh <= 0:
            raise ValueError("tou_price_gbp_per_kwh must be > 0")

        if fit_price_gbp_per_kwh > tou_price_gbp_per_kwh:
            raise ValueError("fit_price_gbp_per_kwh must be <= tou_price_gbp_per_kwh")

        self.fit_price_gbp_per_kwh = fit_price_gbp_per_kwh
        self.tou_price_gbp_per_kwh = tou_price_gbp_per_kwh

        return generate_price(self)

    def update_from_market_signal(self, signal: MarketSignal) -> bool:
        update_zip(self, signal)
        return True

    def state_dict(self) -> dict:
        return {
            "h_id": self.h_id,
            "side": self.side,
            "beta": self.beta,
            "gamma": self.gamma,
            "margin": self.margin,
            "last_margin_adjustment": self.last_margin_adjustment,
            "fit_price_gbp_per_kwh": self.fit_price_gbp_per_kwh,
            "tou_price_gbp_per_kwh": self.tou_price_gbp_per_kwh,
        }


def suggest_action(side: str, submitted_price_gbp_per_kwh: float, reference_price_gbp_per_kwh: float) -> str:
    """
    Helper kept for compatibility with current cda.py import.

    seller:
        if p <= q -> raise
        else      -> lower

    buyer:
        if p >= q -> raise
        else      -> lower
    """
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    p = submitted_price_gbp_per_kwh
    q = reference_price_gbp_per_kwh

    if side == "sell":
        return "raise" if p <= q else "lower"

    return "raise" if p >= q else "lower"