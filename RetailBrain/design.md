# RetailBrain - Design Document

## System Architecture

### Architecture Overview

RetailBrain follows a client-server architecture with a clear separation between frontend presentation and backend business logic.

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (SPA)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │Dashboard │  │ Copilot  │  │ Forecast │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                         │                                    │
│                    app.js (API Client)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/JSON
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    main.py (API Layer)                │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │  │
│  │  │ Upload │  │Metrics │  │Forecast│  │Copilot │    │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer (Business Logic)           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│  │  │ analytics.py │  │forecasting.py│  │copilot.py │ │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Store (In-Memory)                   │  │
│  │                  DATASTORE = {"df": None}             │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ API Call
                           ▼
                  ┌─────────────────────┐
                  │  Hugging Face API   │
                  │  (Kimi-K2-Instruct) │
                  └─────────────────────┘
```

## Component Design

### 1. Frontend Components

#### 1.1 Single Page Application Structure

The frontend uses a simple page-switching mechanism without a framework:

- **Navigation**: Sidebar with links to four main sections
- **Page Management**: JavaScript function `showPage()` toggles visibility
- **State Management**: Minimal state stored in DOM and API responses

#### 1.2 Page Components

**Home Page**
- Purpose: CSV file upload interface
- Elements: File input, upload button, status display
- Interactions: File selection, upload trigger, success/error feedback

**Dashboard Page**
- Purpose: Comprehensive sales and inventory analytics
- Sections:
  - KPI Cards: Revenue, units, trend, product count
  - Product Leaders: Top and slow performers with top 5 list
  - Inventory Health: Stock categorization and alerts
- Data Flow: Fetches from `/dashboard/metrics` endpoint
- Refresh: Manual refresh button

**AI Copilot Page**
- Purpose: Conversational AI interface for business insights
- Elements: Chat history display, message input, send button
- Interactions: User types query, system appends messages, scrolls to bottom
- Message Types: User messages (right-aligned), assistant messages (left-aligned)

**Forecast Page**
- Purpose: Demand forecasting and inventory planning
- Inputs: Product selector, forecast days, lead time, service level
- Output: Forecast summary, risk assessment, daily forecast table
- Data Flow: Fetches from `/forecast` endpoint with query parameters

#### 1.3 Styling Architecture

- **Framework**: Bootstrap 5.3 for base components and grid
- **Custom CSS**: `styles.css` for brand-specific styling
- **Color Scheme**:
  - Primary: Blue (#007bff)
  - Success: Green (positive trends)
  - Warning: Orange (medium risk)
  - Danger: Red (critical alerts)
- **Layout**: Flexbox-based sidebar + main content area

### 2. Backend Components

#### 2.1 API Layer (main.py)

**Responsibilities**:
- HTTP request handling
- CORS configuration
- Data store management
- Request validation
- Response formatting

**Endpoints**:

```python
POST /upload
- Input: Multipart form data with CSV file
- Output: {message: str, rows: int}
- Side Effect: Updates DATASTORE["df"]

GET /dashboard/metrics
- Input: None (uses DATASTORE)
- Output: Dashboard metrics JSON
- Error: {error: str} if no data

GET /forecast
- Input: Query params (product, days, lead_time_days, service_level)
- Output: Forecast data with daily predictions and summary
- Error: {error: str} for validation or data issues

GET /products
- Input: None (uses DATASTORE)
- Output: {products: [str]}
- Error: {error: str, products: []} if no data

POST /copilot/chat
- Input: Query param (query: str)
- Output: {answer: str, provider: str, context_used: dict}
- Error: {answer: str, error: str} with fallback message
```

**CORS Configuration**:
- Allowed origins: localhost:5500, 127.0.0.1:5500
- Allows credentials, all methods, all headers

#### 2.2 Analytics Service (analytics.py)

**Purpose**: Calculate business metrics and insights from sales data

**Key Functions**:

```python
get_dashboard_metrics(df: DataFrame) -> dict
```

**Processing Pipeline**:
1. Data preparation: Parse dates, calculate revenue
2. Aggregate metrics: Sum revenue, count units, calculate averages
3. Product analysis: Group by product, rank by performance
4. Inventory assessment: Categorize stock levels, identify alerts
5. Trend calculation: Compare first half vs second half of period
6. Best day identification: Find peak revenue day

**Output Structure**:
- overview: Total metrics and trend
- leaders: Top and slow products
- top_products: Top 5 ranked list
- inventory: Stock health and alerts
- highlights: Best performing day

**Design Decisions**:
- Uses pandas for efficient data manipulation
- Handles missing data with safe float conversion
- Sorts products by units sold for ranking
- Stock thresholds: Critical <10, Warning 10-24, Healthy ≥25

#### 2.3 Forecasting Service (forecasting.py)

**Purpose**: Generate demand forecasts and inventory recommendations

**Forecasting Models**:

1. **Simple Mean**: Average of historical sales
2. **Weighted Moving Average**: Recent data weighted more heavily
3. **Trend Regression**: Linear regression to project trend

**Model Selection Process**:
1. Split data: 80% training, 20% testing
2. Generate predictions for test period using each model
3. Calculate MAE (Mean Absolute Error) for each model
4. Select model with lowest MAE
5. Use selected model for future predictions

**Inventory Calculations**:

```
Lead Time Demand = Avg Daily Demand × Lead Time Days
Safety Stock = Z-Score × Demand Std Dev × √(Lead Time Days)
Reorder Point = Lead Time Demand + Safety Stock
Suggested Order = max(0, Reorder Point - Current Stock)
Days of Cover = Current Stock / Avg Daily Demand
```

**Service Level Z-Scores**:
- 80%: 0.84
- 85%: 1.04
- 90%: 1.28
- 95%: 1.64
- 98%: 2.05
- 99%: 2.33

**Risk Assessment**:
- High: Days of cover ≤ lead time
- Medium: Days of cover ≤ lead time × 1.5
- Low: Days of cover > lead time × 1.5

**Design Decisions**:
- Requires minimum 5 days of history for trend analysis
- Fills missing dates with zero sales
- Confidence intervals based on historical variability
- Validates input ranges (1-90 days)

#### 2.4 AI Copilot Service (copilot.py)

**Purpose**: Provide natural language interface to data insights

**Architecture**:

```
User Query
    ↓
Summarize Data (Quick Insights)
    ↓
Build Dataset Profile (Column Statistics)
    ↓
Retrieve Relevant Rows (Smart Sampling)
    ↓
Build Context JSON (Within Token Limits)
    ↓
Generate System Prompt
    ↓
Call Hugging Face API (Kimi-K2-Instruct)
    ↓
Return Answer + Context Metadata
```

**Context Building Strategy**:

1. **Dataset Profile**: Statistical summary of each column
   - Numeric: count, min, max, mean
   - Categorical: count, unique values, top 10 values

2. **Row Retrieval**: Intelligent sampling to stay within token limits
   - Tokenize query into search terms
   - Score each row based on term matches
   - Select top-scoring rows (up to 250)
   - Fill remaining quota with evenly-spaced rows
   - Shrink if context exceeds 65,000 characters

3. **Context Payload**:
   ```json
   {
     "rows_scanned": int,
     "dataset_profile": {...},
     "retrieved_rows": [...]
   }
   ```

**Prompt Engineering**:

System prompt includes:
- Role definition (AI retail copilot)
- Business context (revenue, top/slow products, low stock)
- Dataset structure (columns, row counts)
- Data context (JSON with profile and rows)
- Instructions (actionable recommendations, bullet points)

**AI Model Configuration**:
- Provider: Hugging Face Inference API
- Model: moonshotai/Kimi-K2-Instruct-0905
- Temperature: 0.3 (focused, deterministic responses)
- API: OpenAI-compatible interface

**Error Handling**:
- Graceful fallback if API fails
- Returns error message with context metadata
- Ensures "answer" field always present in response

**Design Decisions**:
- Token budget: 65,000 characters for context
- Minimum rows: 25 (ensures some data always included)
- Maximum rows: 250 (balances detail vs token usage)
- Retrieval strategy: Hybrid (relevance + coverage)

### 3. Data Flow

#### 3.1 Upload Flow

```
User selects CSV → Frontend sends FormData → Backend parses CSV
→ Validates columns → Stores in DATASTORE → Returns row count
→ Frontend displays success → Loads product list
```

#### 3.2 Dashboard Flow

```
User navigates to Dashboard → Frontend calls /dashboard/metrics
→ Backend processes data through analytics service
→ Returns metrics JSON → Frontend updates all KPI cards and lists
```

#### 3.3 Forecast Flow

```
User selects product and parameters → Frontend calls /forecast
→ Backend validates inputs → Prepares daily series
→ Selects best model → Generates predictions
→ Calculates inventory recommendations → Returns forecast JSON
→ Frontend renders summary and table
```

#### 3.4 Copilot Flow

```
User types question → Frontend appends to chat → Calls /copilot/chat
→ Backend summarizes data → Builds context with retrieval
→ Calls Hugging Face API → Receives AI response
→ Returns answer with metadata → Frontend appends assistant message
```

## Data Models

### CSV Input Schema

```
date: string (YYYY-MM-DD)
product: string
sales: number (units sold)
price: number (unit price)
stock: number (current inventory)
```

### Dashboard Metrics Response

```json
{
  "overview": {
    "total_revenue": float,
    "total_units_sold": int,
    "avg_unit_price": float,
    "total_products": int,
    "sales_trend_pct": float
  },
  "leaders": {
    "top_product": {
      "name": string,
      "units_sold": int,
      "revenue": float
    },
    "slow_product": {
      "name": string,
      "units_sold": int,
      "revenue": float
    }
  },
  "top_products": [
    {
      "name": string,
      "units_sold": int,
      "revenue": float,
      "stock": int
    }
  ],
  "inventory": {
    "stock_health": {
      "critical": int,
      "warning": int,
      "healthy": int
    },
    "alerts": [
      {
        "name": string,
        "stock": int
      }
    ]
  },
  "highlights": {
    "best_day": {
      "date": string,
      "revenue": float
    }
  }
}
```

### Forecast Response

```json
{
  "product": string,
  "model": string,
  "forecast_days": int,
  "lead_time_days": int,
  "service_level": float,
  "daily_forecast": [
    {
      "date": string,
      "forecast": int,
      "lower": int,
      "upper": int
    }
  ],
  "summary": {
    "avg_daily_demand": float,
    "total_forecast_demand": int,
    "current_stock": int,
    "reorder_point": int,
    "suggested_order_qty": int,
    "estimated_days_of_cover": float,
    "stockout_risk": string,
    "safety_stock": int,
    "demand_std_dev": float
  },
  "accuracy": {
    "mae": float,
    "mape": float
  }
}
```

### Copilot Response

```json
{
  "answer": string,
  "provider": string,
  "context_used": {
    "total_revenue": float,
    "top_product": string,
    "slow_mover": string,
    "low_stock_products": [string],
    "rows_scanned": int,
    "rows_sent_to_model": int
  },
  "error": string (optional)
}
```

## Security Considerations

### Authentication & Authorization
- Current: No authentication (single-user session)
- Future: Add user authentication and session management

### Data Protection
- API keys stored in .env file (not committed to version control)
- CORS restricts API access to specific origins
- No sensitive data persisted to disk

### Input Validation
- File type validation for CSV uploads
- Numeric range validation for forecast parameters
- Query parameter sanitization
- DataFrame column validation

### Error Handling
- No stack traces exposed to frontend
- Generic error messages for security issues
- Graceful degradation for service failures

## Performance Optimization

### Backend
- Pandas vectorized operations for data processing
- In-memory data store for fast access
- Efficient aggregation using groupby operations
- Model selection caching within forecast calculation

### Frontend
- Minimal JavaScript framework overhead
- Lazy loading of product list
- Manual refresh to avoid unnecessary API calls
- Efficient DOM manipulation

### AI Copilot
- Token budget management to prevent timeouts
- Intelligent row sampling to reduce context size
- Low temperature for faster, focused responses
- Fallback mechanism for service unavailability

## Scalability Considerations

### Current Limitations
- Single in-memory data store (no multi-user support)
- No data persistence across sessions
- Synchronous request processing
- Limited to datasets that fit in memory

### Future Improvements
- Database integration (PostgreSQL, MongoDB)
- Redis caching for frequently accessed metrics
- Async processing for long-running forecasts
- Background job queue for AI requests
- Horizontal scaling with load balancer
- Multi-tenant data isolation

## Technology Stack Rationale

### Backend: FastAPI
- Fast, modern Python web framework
- Automatic API documentation (OpenAPI)
- Built-in data validation with Pydantic
- Async support for future scalability
- Easy CORS configuration

### Data Processing: Pandas + NumPy
- Industry standard for data manipulation
- Efficient vectorized operations
- Rich ecosystem of statistical functions
- Easy CSV parsing and transformation

### AI: Hugging Face + OpenAI SDK
- Access to state-of-the-art language models
- OpenAI-compatible API for easy integration
- Cost-effective inference routing
- Flexible model selection

### Frontend: Vanilla JavaScript + Bootstrap
- No build process required
- Fast development iteration
- Minimal dependencies
- Responsive design out of the box
- Easy to understand and maintain

## Deployment Architecture

### Development Environment
```
Frontend: Live Server (port 5500)
Backend: Uvicorn (port 8000)
```

### Production Recommendations
```
Frontend: Nginx static file server
Backend: Gunicorn + Uvicorn workers
Reverse Proxy: Nginx
SSL: Let's Encrypt
Monitoring: Prometheus + Grafana
Logging: ELK Stack
```

## Testing Strategy

### Unit Tests
- Analytics calculations
- Forecasting model selection
- Context building logic
- Input validation

### Integration Tests
- API endpoint responses
- Service layer interactions
- Error handling flows

### End-to-End Tests
- File upload workflow
- Dashboard data display
- Forecast generation
- Copilot conversation

### Performance Tests
- Large dataset handling (10k+ rows)
- Concurrent user simulation
- API response time benchmarks
- Memory usage profiling
