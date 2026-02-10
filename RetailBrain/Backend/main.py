from fastapi import FastAPI, UploadFile, File
import pandas as pd
from Services.analytics import get_dashboard_metrics
from Services.forecasting import get_forecast
from Services.copilot import chat_with_copilot

app = FastAPI()
DATASTORE = {"df": None}

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
def forecast(product: str, days: int = 7):
    if DATASTORE["df"] is None:
        return {"error": "No data uploaded"}
    return get_forecast(DATASTORE["df"], product, days)

@app.post("/copilot/chat")
def copilot_chat(query: str):
    if DATASTORE["df"] is None:
        return {"error": "No data uploaded"}
    return chat_with_copilot(DATASTORE["df"], query)
