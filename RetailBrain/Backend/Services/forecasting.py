import math
from datetime import timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

SERVICE_LEVEL_Z = {
    0.80: 0.84,
    0.85: 1.04,
    0.90: 1.28,
    0.95: 1.64,
    0.98: 2.05,
    0.99: 2.33,
}


def _prepare_daily_series(df: pd.DataFrame, product: str) -> Tuple[pd.Series, float]:
    product_df = df[df["product"] == product].copy()
    if product_df.empty:
        raise ValueError("Product not found")

    product_df["date"] = pd.to_datetime(product_df["date"], errors="coerce")
    product_df = product_df.dropna(subset=["date"]).sort_values("date")
    if product_df.empty:
        raise ValueError("No valid date values found for selected product")

    last_known_stock = float(product_df.iloc[-1]["stock"]) if "stock" in product_df.columns else 0.0

    daily = product_df.groupby(product_df["date"].dt.date)["sales"].sum().sort_index()
    if daily.empty:
        raise ValueError("No sales history found for selected product")

    idx = pd.date_range(start=pd.Timestamp(daily.index.min()), end=pd.Timestamp(daily.index.max()), freq="D")
    daily = daily.reindex(idx.date, fill_value=0)
    daily.index = idx

    return daily.astype(float), last_known_stock


def _weighted_ma(values: np.ndarray, window: int = 14) -> float:
    if len(values) == 0:
        return 0.0
    tail = values[-min(window, len(values)):]
    weights = np.arange(1, len(tail) + 1, dtype=float)
    return float(np.dot(tail, weights) / weights.sum())


def _trend_projection(values: np.ndarray) -> float:
    n = len(values)
    if n < 5:
        return float(np.mean(values)) if n > 0 else 0.0

    x = np.arange(n, dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    next_value = intercept + slope * n
    return float(max(0.0, next_value))


def _mape(actual: np.ndarray, pred: np.ndarray) -> float:
    denom = np.where(actual == 0, 1.0, actual)
    return float(np.mean(np.abs((actual - pred) / denom)) * 100.0)


def _mae(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - pred)))


def _select_model(series: pd.Series) -> Tuple[str, float, Dict]:
    values = series.values.astype(float)
    if len(values) < 8:
        base = float(np.mean(values)) if len(values) > 0 else 0.0
        return "mean", base, {"mae": 0.0, "mape": 0.0}

    split = max(int(len(values) * 0.8), len(values) - 7)
    train = values[:split]
    test = values[split:]

    mean_pred = np.full_like(test, fill_value=float(np.mean(train)), dtype=float)
    wma_pred = np.full_like(test, fill_value=_weighted_ma(train), dtype=float)
    trend_pred = np.full_like(test, fill_value=_trend_projection(train), dtype=float)

    candidates = {
        "mean": {"pred": mean_pred},
        "weighted_moving_average": {"pred": wma_pred},
        "trend_regression": {"pred": trend_pred},
    }

    for name, payload in candidates.items():
        payload["mae"] = _mae(test, payload["pred"])
        payload["mape"] = _mape(test, payload["pred"])

    best_name = min(candidates.keys(), key=lambda n: candidates[n]["mae"])
    if best_name == "mean":
        base = float(np.mean(values))
    elif best_name == "weighted_moving_average":
        base = _weighted_ma(values)
    else:
        base = _trend_projection(values)

    best = candidates[best_name]
    return best_name, float(base), {"mae": round(best["mae"], 2), "mape": round(best["mape"], 2)}


def _service_level_z(service_level: float) -> float:
    return SERVICE_LEVEL_Z.get(service_level, 1.64)


def get_forecast(
    df: pd.DataFrame,
    product: str,
    days: int = 7,
    lead_time_days: int = 7,
    service_level: float = 0.95,
):
    if days < 1 or days > 90:
        return {"error": "Days must be between 1 and 90"}

    if lead_time_days < 1 or lead_time_days > 90:
        return {"error": "Lead time must be between 1 and 90 days"}

    try:
        daily_series, current_stock = _prepare_daily_series(df, product)
    except ValueError as exc:
        return {"error": str(exc)}

    model_name, base_daily, accuracy = _select_model(daily_series)

    demand_std = float(daily_series.tail(min(30, len(daily_series))).std(ddof=0))
    demand_std = 0.0 if math.isnan(demand_std) else demand_std

    z = _service_level_z(round(float(service_level), 2))
    horizon = pd.date_range(start=daily_series.index[-1] + timedelta(days=1), periods=days, freq="D")

    daily_forecast: List[Dict] = []
    for forecast_date in horizon:
        expected = max(0.0, base_daily)
        interval_margin = z * demand_std
        lower = max(0.0, expected - interval_margin)
        upper = max(0.0, expected + interval_margin)

        daily_forecast.append(
            {
                "date": forecast_date.strftime("%Y-%m-%d"),
                "forecast": int(round(expected)),
                "lower": int(round(lower)),
                "upper": int(round(upper)),
            }
        )

    avg_daily_demand = float(np.mean([row["forecast"] for row in daily_forecast])) if daily_forecast else 0.0
    total_forecast_demand = int(round(sum(row["forecast"] for row in daily_forecast)))

    lead_time_demand = avg_daily_demand * lead_time_days
    safety_stock = z * demand_std * math.sqrt(lead_time_days)
    reorder_point = int(round(lead_time_demand + safety_stock))
    suggested_order_qty = int(round(max(0.0, reorder_point - current_stock)))

    days_of_cover = (current_stock / avg_daily_demand) if avg_daily_demand > 0 else float("inf")
    if days_of_cover <= lead_time_days:
        stock_risk = "high"
    elif days_of_cover <= lead_time_days * 1.5:
        stock_risk = "medium"
    else:
        stock_risk = "low"

    return {
        "product": product,
        "model": model_name,
        "forecast_days": days,
        "lead_time_days": lead_time_days,
        "service_level": float(service_level),
        "daily_forecast": daily_forecast,
        "summary": {
            "avg_daily_demand": round(avg_daily_demand, 2),
            "total_forecast_demand": total_forecast_demand,
            "current_stock": int(round(current_stock)),
            "reorder_point": reorder_point,
            "suggested_order_qty": suggested_order_qty,
            "estimated_days_of_cover": round(days_of_cover, 1) if math.isfinite(days_of_cover) else None,
            "stockout_risk": stock_risk,
            "safety_stock": int(round(safety_stock)),
            "demand_std_dev": round(demand_std, 2),
        },
        "accuracy": accuracy,
    }
