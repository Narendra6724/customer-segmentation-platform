"""
API Routes — prediction, customer listing, analytics, and CSV upload.
"""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.services import model_service, db_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    customer_id: int | None = Field(None, description="Optional customer ID (auto-assigned if omitted)")
    income: float = Field(..., gt=0, description="Annual income in k$")
    spending: float = Field(..., ge=1, le=100, description="Spending score (1-100)")


class PredictResponse(BaseModel):
    cluster: int
    label: str
    insight: str
    customer_id: int


class CustomerOut(BaseModel):
    id: int
    customer_id: int
    income: float
    spending: float
    cluster: int
    insight: str | None
    created_at: str | None
    updated_at: str | None


class ClusterDistribution(BaseModel):
    cluster: int
    count: int


class ClusterStats(BaseModel):
    cluster: int
    count: int
    avg_income: float
    min_income: float
    max_income: float
    avg_spending: float
    min_spending: float
    max_spending: float


class DetailedAnalytics(BaseModel):
    distribution: list[ClusterDistribution]
    cluster_stats: list[ClusterStats]
    customers: list[CustomerOut]


class UploadSummary(BaseModel):
    inserted: int
    updated: int
    errors: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    """Predict customer cluster, store/update record, and return insight."""
    try:
        result = model_service.predict(req.income, req.spending)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    cust_id = req.customer_id if req.customer_id is not None else db_service.get_next_customer_id(db)

    customer, _ = db_service.upsert_customer(
        db,
        customer_id=cust_id,
        income=req.income,
        spending=req.spending,
        cluster=result["cluster"],
        insight=result["insight"],
    )

    return PredictResponse(
        cluster=result["cluster"],
        label=result["label"],
        insight=result["insight"],
        customer_id=customer.customer_id,
    )


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    """Return all stored customer prediction records."""
    return db_service.get_all_customers(db)


@router.get("/analytics", response_model=list[ClusterDistribution])
def analytics(db: Session = Depends(get_db)):
    """Return cluster distribution counts."""
    return db_service.get_cluster_distribution(db)


@router.get("/analytics/detailed", response_model=DetailedAnalytics)
def detailed_analytics(db: Session = Depends(get_db)):
    """Return enriched analytics for the enterprise dashboard."""
    return db_service.get_detailed_analytics(db)


@router.post("/upload-csv", response_model=UploadSummary)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Bulk import customers from a headerless CSV.
    Expected columns: customer_id, annual_income, spending_score
    Upserts by customer_id — existing records are updated, new ones inserted.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows: list[tuple[int, float, float]] = []
    parse_errors: list[dict] = []

    for i, row in enumerate(reader, start=1):
        # Skip empty lines
        if not row or all(cell.strip() == "" for cell in row):
            continue
        if len(row) < 3:
            parse_errors.append({"row": i, "error": f"Expected 3 columns, got {len(row)}"})
            continue
        try:
            cust_id = int(row[0].strip())
            income = float(row[1].strip())
            spending = float(row[2].strip())
            if spending < 1 or spending > 100:
                parse_errors.append({"row": i, "error": f"Spending score {spending} out of range [1-100]"})
                continue
            if income <= 0:
                parse_errors.append({"row": i, "error": f"Income must be > 0, got {income}"})
                continue
            rows.append((cust_id, income, spending))
        except ValueError as e:
            parse_errors.append({"row": i, "error": f"Parse error: {e}"})

    if not rows and parse_errors:
        raise HTTPException(status_code=400, detail={"message": "No valid rows found.", "errors": parse_errors})

    summary = db_service.bulk_upsert_csv(db, rows)
    summary["errors"].extend(parse_errors)
    return summary
