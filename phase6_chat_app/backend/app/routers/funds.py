"""
Funds Router - REST endpoints for fund data.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from ..models.schemas import FundDetail, FundListResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "phase1_data_collection"))

router = APIRouter(prefix="/funds", tags=["funds"])

# Load fund data
_funds_data: List[dict] = []

def load_funds_data():
    """Load fund data from Phase 1"""
    global _funds_data
    try:
        fund_file = Path(__file__).parent.parent.parent.parent.parent / "phase1_data_collection" / "data" / "processed" / "extracted_funds.json"
        with open(fund_file, 'r', encoding='utf-8') as f:
            _funds_data = json.load(f)
        print(f"✓ Loaded {len(_funds_data)} funds")
    except Exception as e:
        print(f"⚠ Could not load fund data: {e}")
        _funds_data = []

# Load on module import
load_funds_data()


@router.get("", response_model=FundListResponse)
async def list_funds(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    amc: Optional[str] = None
):
    """List all mutual funds with pagination and filtering"""
    funds = _funds_data.copy()
    
    # Apply filters
    if category:
        funds = [f for f in funds if f.get('category', '').lower() == category.lower()]
    
    # Calculate pagination
    total = len(funds)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_funds = funds[start_idx:end_idx]
    
    return FundListResponse(
        funds=paginated_funds,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/search")
async def search_funds(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search funds by name or other attributes"""
    query_lower = q.lower()
    results = []
    
    for fund in _funds_data:
        # Search in fund name
        if query_lower in fund.get('fund_name', '').lower():
            results.append(fund)
        # Search in AMC
        elif query_lower in fund.get('amc', '').lower():
            results.append(fund)
        # Search in category
        elif query_lower in fund.get('category', '').lower():
            results.append(fund)
        
        if len(results) >= limit:
            break
    
    return {"query": q, "results": results, "count": len(results)}


@router.get("/{fund_name}", response_model=FundDetail)
async def get_fund_detail(fund_name: str):
    """Get detailed information about a specific fund"""
    # URL decode and normalize
    fund_name_normalized = fund_name.replace('-', ' ').lower()
    
    for fund in _funds_data:
        if fund.get('fund_name', '').lower() == fund_name_normalized or \
           fund_name_normalized in fund.get('fund_name', '').lower():
            return FundDetail(**fund)
    
    raise HTTPException(status_code=404, detail=f"Fund '{fund_name}' not found")


@router.get("/categories/list")
async def get_categories():
    """Get list of available fund categories"""
    categories = set()
    for fund in _funds_data:
        if fund.get('category'):
            categories.add(fund['category'])
    return {"categories": sorted(list(categories))}
