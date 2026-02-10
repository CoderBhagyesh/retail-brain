import pandas as pd

def get_dashboard_metrics(df: pd.DataFrame):
    total_revenue = (df["sales"] * df["price"]).sum()

    top_product = (
        df.groupby("product")["sales"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )

    slow_mover = (
        df.groupby("product")["sales"]
        .sum()
        .sort_values(ascending=True)
        .index[0]
    )

    low_stock = df[df["stock"] < 10]["product"].unique().tolist()

    return {
        "total_revenue": float(total_revenue),
        "top_product": top_product,
        "slow_mover": slow_mover,
        "low_stock_products": low_stock
    }
