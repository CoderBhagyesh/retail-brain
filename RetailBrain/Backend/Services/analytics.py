import pandas as pd


def _safe_float(value):
    return float(value) if pd.notna(value) else 0.0


def _to_daily_sales(df: pd.DataFrame) -> pd.Series:
    daily = df.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"])
    daily["revenue"] = daily["sales"] * daily["price"]
    if daily.empty:
        return pd.Series(dtype="float64")
    return daily.groupby(daily["date"].dt.date)["revenue"].sum().sort_index()


def get_dashboard_metrics(df: pd.DataFrame):
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.sort_values("date")
    data["revenue"] = data["sales"] * data["price"]

    total_revenue = _safe_float(data["revenue"].sum())
    total_units = int(data["sales"].sum())
    avg_unit_price = _safe_float(data["price"].mean())
    total_products = int(data["product"].nunique())

    by_product = (
        data.groupby("product", as_index=False)
        .agg(
            units_sold=("sales", "sum"),
            revenue=("revenue", "sum"),
            latest_stock=("stock", "last"),
        )
        .sort_values("units_sold", ascending=False)
    )

    if by_product.empty:
        return {"error": "No product data found"}

    top_product_row = by_product.iloc[0]
    slow_product_row = by_product.sort_values("units_sold", ascending=True).iloc[0]

    top_products = by_product.head(5).to_dict(orient="records")
    low_stock_items = by_product[by_product["latest_stock"] < 10]

    stock_health = {
        "critical": int((by_product["latest_stock"] < 10).sum()),
        "warning": int(((by_product["latest_stock"] >= 10) & (by_product["latest_stock"] < 25)).sum()),
        "healthy": int((by_product["latest_stock"] >= 25).sum()),
    }

    daily_revenue = _to_daily_sales(data)
    trend_pct = 0.0
    if len(daily_revenue) >= 4:
        half = len(daily_revenue) // 2
        prev = daily_revenue.iloc[:half].mean()
        curr = daily_revenue.iloc[half:].mean()
        if prev > 0:
            trend_pct = ((curr - prev) / prev) * 100.0

    best_day = None
    if not daily_revenue.empty:
        best_day_idx = daily_revenue.idxmax()
        best_day = {
            "date": str(best_day_idx),
            "revenue": _safe_float(daily_revenue.max()),
        }

    return {
        "overview": {
            "total_revenue": round(total_revenue, 2),
            "total_units_sold": total_units,
            "avg_unit_price": round(avg_unit_price, 2),
            "total_products": total_products,
            "sales_trend_pct": round(trend_pct, 2),
        },
        "leaders": {
            "top_product": {
                "name": str(top_product_row["product"]),
                "units_sold": int(top_product_row["units_sold"]),
                "revenue": round(_safe_float(top_product_row["revenue"]), 2),
            },
            "slow_product": {
                "name": str(slow_product_row["product"]),
                "units_sold": int(slow_product_row["units_sold"]),
                "revenue": round(_safe_float(slow_product_row["revenue"]), 2),
            },
        },
        "top_products": [
            {
                "name": str(item["product"]),
                "units_sold": int(item["units_sold"]),
                "revenue": round(_safe_float(item["revenue"]), 2),
                "stock": int(item["latest_stock"]),
            }
            for item in top_products
        ],
        "inventory": {
            "stock_health": stock_health,
            "alerts": [
                {
                    "name": str(item["product"]),
                    "stock": int(item["latest_stock"]),
                }
                for _, item in low_stock_items.iterrows()
            ],
        },
        "highlights": {
            "best_day": best_day,
        },
    }
