# RetailBrain - Requirements

## Project Overview
RetailBrain is an AI-powered retail analytics and forecasting platform that helps store managers make data-driven decisions through interactive dashboards, sales forecasting, and an AI copilot assistant.

## System Requirements

### Python Version
- Python 3.8 or higher

### Backend Dependencies

#### Core Framework
- `fastapi` - Modern web framework for building APIs
- `uvicorn` - ASGI server for running FastAPI applications

#### Data Processing
- `pandas` - Data manipulation and analysis library
- `python-multipart` - Required for file upload handling in FastAPI

#### AI/ML Integration
- `openai` - OpenAI Python client (used with Hugging Face router)

#### Configuration
- `python-dotenv` - Environment variable management

#### Frontend (Streamlit)
- `streamlit` - Web application framework for the UI
- `requests` - HTTP library for backend API calls

## Environment Variables

Create a `.env` file in the project root with the following:

```
HF_TOKEN=your_huggingface_token_here
```

### Getting a Hugging Face Token
1. Sign up at https://huggingface.co
2. Go to Settings → Access Tokens
3. Create a new token with read permissions
4. Copy the token to your `.env` file

## Installation

### Option 1: Using pip
```bash
pip install fastapi uvicorn pandas python-multipart openai python-dotenv streamlit requests
```

### Option 2: Using requirements.txt
Create a `requirements.txt` file with:
```
fastapi
uvicorn
pandas
python-multipart
openai
python-dotenv
streamlit
requests
```

Then install:
```bash
pip install -r requirements.txt
```

## Running the Application

### Start Backend Server
```bash
cd RetailBrain/Backend
uvicorn main:app --reload --port 8000
```

### Start Frontend (Streamlit)
```bash
cd RetailBrain/Frontend
streamlit run app.py
```

### Alternative Frontend (HTML/JS)
Open `RetailBrain/Frontend/index.html` in a browser using a local server:
```bash
cd RetailBrain/Frontend
python -m http.server 5500
```

## API Endpoints

### POST /upload
Upload CSV file with sales data

### GET /dashboard/metrics
Retrieve dashboard analytics (revenue, top products, low stock)

### GET /forecast
Get sales forecast for a specific product
- Parameters: `product` (string), `days` (int, default: 7)

### POST /copilot/chat
Chat with AI copilot for business insights
- Parameters: `query` (string)

## Data Format

The application expects CSV files with the following columns:
- `date` - Transaction date
- `product` - Product name
- `sales` - Number of units sold
- `price` - Unit price
- `stock` - Current stock level

Sample data is provided in `RetailBrain/Data/sample_sales.csv`

## CORS Configuration

The backend is configured to accept requests from:
- http://127.0.0.1:5500
- http://localhost:5500

Modify `main.py` to add additional origins if needed.

## AI Model

The copilot uses Hugging Face's router with the `moonshotai/Kimi-K2-Instruct-0905` model. The system includes fallback handling if the AI service is unavailable.

## Features

1. **Dashboard Analytics**
   - Total revenue calculation
   - Top-selling product identification
   - Slow-moving product detection
   - Low stock alerts (threshold: < 10 units)

2. **Sales Forecasting**
   - 7-day moving average prediction
   - Customizable forecast period
   - Product-specific forecasts

3. **AI Copilot**
   - Natural language queries
   - Actionable business recommendations
   - Context-aware responses based on current data

## Development Notes

- The backend uses an in-memory datastore (`DATASTORE`) for uploaded CSV data
- Data persists only during the server session
- For production, consider implementing persistent storage (database)
- The AI copilot requires a valid Hugging Face token to function
