import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client():
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN not found in .env")
    
    # Hugging Face OpenAI-compatible router
    return OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=hf_token,
    )

def summarize_data(df: pd.DataFrame):
    total_revenue = float((df["sales"] * df["price"]).sum())
    top_product = df.groupby("product")["sales"].sum().sort_values(ascending=False).index[0]
    slow_mover = df.groupby("product")["sales"].sum().sort_values(ascending=True).index[0]
    low_stock = df[df["stock"] < 10]["product"].unique().tolist()

    return {
        "total_revenue": total_revenue,
        "top_product": top_product,
        "slow_mover": slow_mover,
        "low_stock_products": low_stock
    }

def chat_with_copilot(df: pd.DataFrame, query: str):
    insights = summarize_data(df)

    system_prompt = f"""
You are an AI retail copilot helping a store manager make decisions.

Business context:
- Total Revenue: {insights["total_revenue"]}
- Top Product: {insights["top_product"]}
- Worst Product: {insights["slow_mover"]}
- Low Stock Products: {insights["low_stock_products"]}

Give actionable recommendations in bullet points.
"""

    try:
        client = get_client()

        response = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User question: {query}"},
            ],
            temperature=0.3,
        )

        return {
            "answer": response.choices[0].message.content,
            "provider": "huggingface",
            "context_used": insights
        }

    except Exception as e:
        print("HF AI ERROR >>>", repr(e))
        return {
            "answer": "AI service unavailable. Showing best recommendations based on current analytics.",
            "error": str(e),
            "provider": "fallback",
            "context_used": insights
        }
