"""Analytics API router for querying precomputed analytical marts and dashboard views."""

import csv
import io
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from apps.api.dependencies.auth import get_current_user, get_export_user, require_roles
from packages.core.schemas.common import DataEnvelope
from packages.core.services.analytics_dashboard_service import (
    calculate_what_if_scenario,
    get_actionable_recommendations,
    get_customer_intelligence_summary,
    get_data_science_arena_summary,
    get_demand_and_pricing_summary,
    get_executive_summary,
    get_global_filter_options,
    get_menu_intelligence_summary,
    get_promotions_and_basket_summary,
    get_ratings_and_anomalies_summary,
    get_sales_and_operations_summary,
    get_wastage_and_inventory_summary,
)
from packages.core.services.mart_reader import (
    MartNotFoundError,
    check_marts_availability,
    read_mart_records,
)
from packages.db.models.auth import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class WhatIfRequest(BaseModel):
    item_id: str = Field(..., description="Target menu item ID (e.g. DISH-0001)")
    price_change_pct: float = Field(0.0, description="Percentage change in price (-50% to +50%)")
    discount_change_pct: float = Field(
        0.0, description="Percentage change in discount rate (-100% to +100%)"
    )
    waste_reduction_pct: float = Field(
        0.0, description="Target reduction in wastage (-50% to +100%)"
    )


@router.get(
    "/status",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_analytics_status(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DataEnvelope[dict[str, Any]]:
    """Return status and availability of analytical marts on disk."""
    availability = check_marts_availability()
    return DataEnvelope(data=availability)


@router.get(
    "/filters",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_filters(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DataEnvelope[dict[str, Any]]:
    """Return global filter lookup dimensions (locations, categories, channels)."""
    options = get_global_filter_options()
    return DataEnvelope(data=options)


@router.get(
    "/executive-summary",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_executive_kpis(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
) -> DataEnvelope[dict[str, Any]]:
    """Compute and return top-level executive KPIs from analytical marts."""
    summary = get_executive_summary()
    return DataEnvelope(data=summary)


@router.get(
    "/menu",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_menu_intelligence(
    current_user: Annotated[
        User, Depends(require_roles("Admin", "StoreManager", "DataScientist", "Cashier"))
    ],
    category_id: str | None = Query(None, description="Category filter"),
    restaurant_id: str | None = Query(None, description="Restaurant filter"),
    classification: str | None = Query(None, description="Classification filter"),
    flag: str | None = Query(None, description="Flag filter name"),
    search: str | None = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> DataEnvelope[dict[str, Any]]:
    """Query menu performance mart with classification, composite scores, and flags."""
    res = get_menu_intelligence_summary(
        category_id=category_id,
        restaurant_id=restaurant_id,
        classification=classification,
        flag=flag,
        search=search,
        limit=limit,
        offset=offset,
    )
    return DataEnvelope(data=res, meta={"limit": limit, "offset": offset})


@router.get(
    "/customers",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_customer_intelligence(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
    segment: str | None = Query(None, description="RFM Segment filter"),
    search: str | None = Query(None, description="Search customer name or ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> DataEnvelope[dict[str, Any]]:
    """Query RFM customer segmentation and churn risk predictions."""
    res = get_customer_intelligence_summary(
        segment=segment,
        search=search,
        limit=limit,
        offset=offset,
    )
    return DataEnvelope(data=res, meta={"limit": limit, "offset": offset})


@router.get(
    "/sales",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_sales_operations(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
    restaurant_id: str | None = Query(None, description="Restaurant filter"),
) -> DataEnvelope[dict[str, Any]]:
    """Query sales patterns, peak periods, channel share, and location rankings."""
    res = get_sales_and_operations_summary(restaurant_id=restaurant_id)
    return DataEnvelope(data=res)


@router.get(
    "/demand",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_demand_pricing(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
    menu_item_id: str | None = Query(None, description="Menu item ID"),
    restaurant_id: str | None = Query(None, description="Restaurant ID"),
) -> DataEnvelope[dict[str, Any]]:
    """Query demand forecast vs actuals and price elasticity analysis."""
    res = get_demand_and_pricing_summary(
        menu_item_id=menu_item_id,
        restaurant_id=restaurant_id,
    )
    return DataEnvelope(data=res)


@router.get(
    "/wastage",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_wastage_inventory(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
    restaurant_id: str | None = Query(None, description="Restaurant ID"),
) -> DataEnvelope[dict[str, Any]]:
    """Query wastage causes, high-risk items, and trends."""
    res = get_wastage_and_inventory_summary(restaurant_id=restaurant_id)
    return DataEnvelope(data=res)


@router.get(
    "/promotions",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_promotions_basket(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
) -> DataEnvelope[dict[str, Any]]:
    """Query promotion impact, traps, and market basket association rules."""
    res = get_promotions_and_basket_summary()
    return DataEnvelope(data=res)


@router.get(
    "/anomalies",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_ratings_anomalies(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
) -> DataEnvelope[dict[str, Any]]:
    """Query sales and rating anomaly event streams."""
    res = get_ratings_and_anomalies_summary()
    return DataEnvelope(data=res)


@router.get(
    "/comparison",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_comparison_arena(
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    task: str | None = Query(
        None, description="Task: demand_forecast, wastage_risk, churn_risk, customer_segmentation"
    ),
    limit: int = Query(50, ge=1, le=500),
) -> DataEnvelope[dict[str, Any]]:
    """Query Data Science Arena cross-pipeline Spark vs Python evaluation metrics and agreement."""
    res = get_data_science_arena_summary(task=task, limit=limit)
    return DataEnvelope(data=res)


@router.get(
    "/recommendations",
    response_model=DataEnvelope[list[dict[str, Any]]],
    status_code=status.HTTP_200_OK,
)
def get_recommendations_feed(
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
) -> DataEnvelope[list[dict[str, Any]]]:
    """Retrieve actionable, evidence-based recommendations derived from analytical marts."""
    recs = get_actionable_recommendations()
    return DataEnvelope(data=recs, meta={"count": len(recs)})


@router.post(
    "/what-if",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def run_what_if_scenario(
    payload: WhatIfRequest,
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager", "DataScientist"))],
) -> DataEnvelope[dict[str, Any]]:
    """Simulate scenario changes using empirical price elasticity estimates."""
    result = calculate_what_if_scenario(
        item_id=payload.item_id,
        price_change_pct=payload.price_change_pct,
        discount_change_pct=payload.discount_change_pct,
        waste_reduction_pct=payload.waste_reduction_pct,
    )
    return DataEnvelope(data=result)


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
)
def export_mart_csv(
    current_user: Annotated[User, Depends(get_export_user)],
    mart_path: str = Query(..., description="Relative path to Parquet mart"),
    limit: int = Query(5000, ge=1, le=50000),
) -> StreamingResponse:
    """Export analytical mart records as downloadable CSV."""
    try:
        records = read_mart_records(mart_relative_path=mart_path, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not records:
        raise HTTPException(status_code=404, detail="No records found to export")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    for row in records:
        writer.writerow(row)
    output.seek(0)

    filename = Path(mart_path).stem + ".csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/mart",
    response_model=DataEnvelope[list[dict[str, Any]]],
    status_code=status.HTTP_200_OK,
)
def query_analytical_mart(
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    mart_path: str = Query(..., description="Relative path to precomputed mart Parquet file"),
    limit: int = Query(100, ge=1, le=1000),
) -> DataEnvelope[list[dict[str, Any]]]:
    """Query precomputed analytical mart records directly via PyArrow."""
    try:
        records = read_mart_records(mart_relative_path=mart_path, limit=limit)
    except MartNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return DataEnvelope(data=records, meta={"count": len(records), "mart_path": mart_path})
