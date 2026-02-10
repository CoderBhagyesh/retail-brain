import pandas as pd

def chat_with_copilot(df: pd.DataFrame, query: str):
    q = query.lower()

    if "restock" in q:
        low_stock = df[df["stock"] < 10]["product"].unique().tolist()
        return {
            "answer": f"These products are low in stock and should be restocked: {low_stock}"
        }

    if "underperform" in q or "worst" in q:
        slow = (
            df.groupby("product")["sales"]
            .sum()
            .sort_values(ascending=True)
            .index[0]
        )
        return {
            "answer": f"The worst performing product is {slow}. Consider discounting or bundling it."
        }

    return {
        "answer": "I can help with restocking, underperforming products, and forecasting. Try asking about those."
    }
