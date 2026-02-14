import pandas as pd
import os
import json
import re
from typing import Dict, List, Set, Tuple
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAX_CONTEXT_CHARS = 65000
MAX_RETRIEVED_ROWS = 250
MIN_RETRIEVED_ROWS = 25

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

def build_full_data_context(df: pd.DataFrame) -> List[Dict]:
    safe_df = df.where(pd.notnull(df), None)
    return safe_df.to_dict(orient="records")

def build_dataset_profile(df: pd.DataFrame) -> dict:
    profile = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            numeric = series.dropna()
            if numeric.empty:
                profile[column] = {"type": "numeric", "count": 0}
            else:
                profile[column] = {
                    "type": "numeric",
                    "count": int(numeric.count()),
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                    "mean": float(numeric.mean()),
                }
        else:
            text_values = series.dropna().astype(str)
            top_values = text_values.value_counts().head(10).to_dict()
            profile[column] = {
                "type": "categorical",
                "count": int(text_values.count()),
                "unique": int(text_values.nunique()),
                "top_values": top_values,
            }

    return profile

def tokenize_query(query: str) -> Set[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", query.lower())
    return {token for token in tokens if len(token) > 2}

def score_row_for_query(row: Dict, query_terms: Set[str], query_text: str) -> int:
    row_text = " ".join(f"{k} {v}" for k, v in row.items()).lower()
    if not query_terms:
        return 0

    score = sum(row_text.count(term) for term in query_terms)
    if query_text and query_text in row_text:
        score += 5
    return score

def evenly_spaced_indices(total: int, count: int) -> List[int]:
    if total == 0 or count <= 0:
        return []
    if count >= total:
        return list(range(total))

    step = total / count
    return [min(int(i * step), total - 1) for i in range(count)]

def retrieve_relevant_rows(all_rows: List[Dict], query: str, max_rows: int) -> List[Dict]:
    if not all_rows:
        return []

    query_terms = tokenize_query(query)
    query_text = query.strip().lower()

    scored = []
    for idx, row in enumerate(all_rows):
        score = score_row_for_query(row, query_terms, query_text)
        if score > 0:
            scored.append((score, idx))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected_indices = [idx for _, idx in scored[:max_rows]]

    if len(selected_indices) < max_rows:
        needed = max_rows - len(selected_indices)
        for idx in evenly_spaced_indices(len(all_rows), needed):
            if idx not in selected_indices:
                selected_indices.append(idx)
            if len(selected_indices) >= max_rows:
                break

    return [all_rows[idx] for idx in selected_indices]

def build_retrieval_context(df: pd.DataFrame, query: str) -> Tuple[str, int]:
    all_rows = build_full_data_context(df)
    profile = build_dataset_profile(df)

    target_rows = min(MAX_RETRIEVED_ROWS, len(all_rows))
    retrieved_rows = retrieve_relevant_rows(all_rows, query, target_rows)

    context_payload = {
        "rows_scanned": len(all_rows),
        "dataset_profile": profile,
        "retrieved_rows": retrieved_rows,
    }

    context_json = json.dumps(context_payload, ensure_ascii=False, separators=(",", ":"))

    while len(context_json) > MAX_CONTEXT_CHARS and len(retrieved_rows) > MIN_RETRIEVED_ROWS:
        shrink_to = max(MIN_RETRIEVED_ROWS, int(len(retrieved_rows) * 0.8))
        retrieved_rows = retrieved_rows[:shrink_to]
        context_payload["retrieved_rows"] = retrieved_rows
        context_json = json.dumps(context_payload, ensure_ascii=False, separators=(",", ":"))

    return context_json, len(retrieved_rows)

def chat_with_copilot(df: pd.DataFrame, query: str):
    insights = summarize_data(df)
    retrieval_context_json, retrieved_count = build_retrieval_context(df, query)

    system_prompt = f"""
You are an AI retail copilot helping a store manager make decisions.
Use BOTH the summarized insights and the data context below.
The retrieval step has scanned the full dataset and selected relevant rows within a token-safe budget.
When answering, ground conclusions in the provided dataset.
If information is insufficient, say what additional slice is needed.

Business context:
- Total Revenue: {insights["total_revenue"]}
- Top Product: {insights["top_product"]}
- Worst Product: {insights["slow_mover"]}
- Low Stock Products: {insights["low_stock_products"]}

Dataset columns: {list(df.columns)}
Total rows: {len(df)}
Rows sent to model after retrieval: {retrieved_count}
Data context (JSON):
{retrieval_context_json}

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
            "context_used": {
                **insights,
                "rows_scanned": len(df),
                "rows_sent_to_model": retrieved_count,
            }
        }

    except Exception as e:
        print("HF AI ERROR >>>", repr(e))
        return {
            "answer": "AI service unavailable. Showing best recommendations based on current analytics.",
            "error": str(e),
            "provider": "fallback",
            "context_used": {
                **insights,
                "rows_scanned": len(df),
                "rows_sent_to_model": retrieved_count,
            }
        }
