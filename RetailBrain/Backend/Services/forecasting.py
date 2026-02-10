import pandas as pd

def get_forecast(df: pd.DataFrame, product: str, days: int = 7):
    product_df = df[df["product"] == product].sort_values("date")
    if product_df.empty:
        return {"error": "Product not found"}

    avg_daily_sales = product_df["sales"].tail(7).mean()
    forecast = [max(0, round(avg_daily_sales)) for _ in range(days)]

    return {
        "product": product,
        "days": days,
        "forecast": forecast,
        "avg_daily_sales": float(avg_daily_sales)
    }
