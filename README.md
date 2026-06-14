# 🎯 Customer Segmentation AI Platform

A production-grade, modular AI platform that segments customers using K-Means clustering, serves predictions via a FastAPI REST API, stores data in SQLite, and displays analytics in a Streamlit dashboard.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Streamlit   │────▶│   FastAPI     │────▶│   SQLite     │
│  Frontend    │◀────│   Backend     │◀────│   Database   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                     ┌─────▼──────┐
                     │  ML Model  │
                     │  (K-Means) │
                     └────────────┘
```

## Project Structure

```
customer-segmentation-platform/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── routes/predict.py    # API endpoints
│   ├── services/
│   │   ├── model_service.py # ML prediction service
│   │   └── db_service.py    # Database CRUD
│   ├── models/customer.py   # SQLAlchemy ORM model
│   └── database/db.py       # DB engine & session
├── ml/
│   ├── train.py             # Training pipeline
│   ├── model.pkl            # Trained K-Means model (generated)
│   └── scaler.pkl           # Fitted scaler (generated)
├── frontend/
│   └── app.py               # Streamlit dashboard
├── data/
│   └── Mall_Customers.csv   # Sample dataset
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
cd customer-segmentation-platform
pip install -r requirements.txt
```

### 2. Train the ML Model

```bash
python ml/train.py
```

This generates `ml/model.pkl` and `ml/scaler.pkl`.

### 3. Start the Backend API

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Start the Frontend Dashboard

Open a **second terminal** in the project root:

```bash
streamlit run frontend/app.py
```

Dashboard opens at: [http://localhost:8501](http://localhost:8501)

## API Endpoints

| Method | Endpoint     | Description                    |
|--------|-------------|--------------------------------|
| POST   | `/predict`  | Predict cluster + save record  |
| GET    | `/customers`| List all stored customers      |
| GET    | `/analytics`| Cluster distribution counts    |
| GET    | `/health`   | Health check                   |

### Example — POST /predict

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"income": 75, "spending": 85}'
```

Response:
```json
{
  "cluster": 1,
  "label": "Premium Customers",
  "insight": "High income and high spending — your most valuable segment...",
  "customer_id": 1
}
```

## Customer Segments

| Cluster | Label              | Description                              |
|---------|--------------------|------------------------------------------|
| 0       | Average Customers  | Moderate income & spending               |
| 1       | Premium Customers  | High income & high spending              |
| 2       | Target Customers   | Low income but high spending             |
| 3       | Low-value Customers| Low income & low spending                |
| 4       | Risk Customers     | High income but low spending             |

## Tech Stack

- **ML**: scikit-learn (KMeans, StandardScaler)
- **Backend**: FastAPI + Uvicorn
- **Database**: SQLite + SQLAlchemy
- **Frontend**: Streamlit
- **Visualization**: Matplotlib + Seaborn
