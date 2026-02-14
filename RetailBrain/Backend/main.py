from fastapi import FastAPI, UploadFile, File
import pandas as pd
from Services.analytics import get_dashboard_metrics
from Services.forecasting import get_forecast
from Services.copilot import chat_with_copilot
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
DATASTORE = {"df": None}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    DATASTORE["df"] = df
    return {"message": "File uploaded successfully", "rows": len(df)}

@app.get("/dashboard/metrics")
def dashboard_metrics():
    if DATASTORE["df"] is None:
        return {"error": "No data uploaded"}
    return get_dashboard_metrics(DATASTORE["df"])

@app.get("/forecast")
def forecast(
    product: str,
    days: int = 7,
    lead_time_days: int = 7,
    service_level: float = 0.95,
):
    if DATASTORE["df"] is None:
        return {"error": "No data uploaded"}
    return get_forecast(DATASTORE["df"], product, days, lead_time_days, service_level)

@app.get("/products")
def get_products():
    if DATASTORE["df"] is None:
        return {"error": "No data uploaded", "products": []}

    if "product" not in DATASTORE["df"].columns:
        return {"error": "Column 'product' not found", "products": []}

    products = sorted(DATASTORE["df"]["product"].dropna().astype(str).unique().tolist())
    return {"products": products}

@app.post("/copilot/chat")
def copilot_chat(query: str):
    if DATASTORE["df"] is None:
        return {
            "answer": "No data uploaded yet. Please upload a CSV file first.",
            "error": "NO_DATA"
        }

    result = chat_with_copilot(DATASTORE["df"], query)

    # Ensure frontend contract: always has "answer"
    if "answer" not in result:
        return {
            "answer": "Something went wrong while generating AI response.",
            "raw": result
        }

    return result

