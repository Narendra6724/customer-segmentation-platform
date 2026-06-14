"""
Database Service — CRUD helpers for Customer records.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.customer import Customer
from backend.services import model_service


def save_customer(
    db: Session,
    customer_id: int,
    income: float,
    spending: float,
    cluster: int,
    insight: str,
) -> Customer:
    """Insert a new customer prediction record and return it."""
    customer = Customer(
        customer_id=customer_id,
        income=income,
        spending=spending,
        cluster=cluster,
        insight=insight,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def upsert_customer(
    db: Session,
    customer_id: int,
    income: float,
    spending: float,
    cluster: int,
    insight: str,
) -> tuple[Customer, bool]:
    """
    Insert or update a customer by customer_id.
    Returns (customer, was_created).
    """
    existing = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if existing:
        existing.income = income
        existing.spending = spending
        existing.cluster = cluster
        existing.insight = insight
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        customer = Customer(
            customer_id=customer_id,
            income=income,
            spending=spending,
            cluster=cluster,
            insight=insight,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer, True


def get_next_customer_id(db: Session) -> int:
    """Return the next available customer_id (max + 1)."""
    result = db.query(func.max(Customer.customer_id)).scalar()
    return (result or 0) + 1


def get_all_customers(db: Session) -> list[dict]:
    """Return all stored customer records as dicts."""
    rows = db.query(Customer).order_by(Customer.customer_id).all()
    return [row.to_dict() for row in rows]


def get_cluster_distribution(db: Session) -> list[dict]:
    """Return count per cluster."""
    results = (
        db.query(Customer.cluster, func.count(Customer.id).label("count"))
        .group_by(Customer.cluster)
        .order_by(Customer.cluster)
        .all()
    )
    return [{"cluster": r.cluster, "count": r.count} for r in results]


def get_detailed_analytics(db: Session) -> dict:
    """
    Return enriched analytics for the enterprise dashboard:
    - cluster distribution
    - per-cluster statistics (mean/min/max income & spending)
    - all customer records for scatter / box plots
    """
    customers = db.query(Customer).all()
    if not customers:
        return {"distribution": [], "cluster_stats": [], "customers": []}

    # Build per-cluster stats
    from collections import defaultdict
    clusters: dict[int, list] = defaultdict(list)
    for c in customers:
        clusters[c.cluster].append(c)

    cluster_stats = []
    for cid in sorted(clusters.keys()):
        members = clusters[cid]
        incomes = [m.income for m in members]
        spendings = [m.spending for m in members]
        cluster_stats.append({
            "cluster": cid,
            "count": len(members),
            "avg_income": round(sum(incomes) / len(incomes), 2),
            "min_income": min(incomes),
            "max_income": max(incomes),
            "avg_spending": round(sum(spendings) / len(spendings), 2),
            "min_spending": min(spendings),
            "max_spending": max(spendings),
        })

    distribution = [{"cluster": s["cluster"], "count": s["count"]} for s in cluster_stats]
    cust_dicts = [c.to_dict() for c in customers]

    return {
        "distribution": distribution,
        "cluster_stats": cluster_stats,
        "customers": cust_dicts,
    }


def bulk_upsert_csv(db: Session, rows: list[tuple[int, float, float]]) -> dict:
    """
    Bulk upsert from CSV rows: list of (customer_id, income, spending).
    Does NOT delete existing data — inserts new, updates existing by customer_id.
    Returns summary dict.
    """
    inserted = 0
    updated = 0
    errors = []

    for i, (cust_id, income, spending) in enumerate(rows):
        try:
            result = model_service.predict(income, spending)
            _, was_created = upsert_customer(
                db,
                customer_id=cust_id,
                income=income,
                spending=spending,
                cluster=result["cluster"],
                insight=result["insight"],
            )
            if was_created:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            errors.append({"row": i + 1, "customer_id": cust_id, "error": str(e)})

    return {"inserted": inserted, "updated": updated, "errors": errors}
