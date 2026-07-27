"""
Business Intelligence Service.

Computes analytical metrics, pipeline summaries, execution status breakdowns,
overdue work order alerts, top customer rankings, pending invoice lists,
and revenue summaries over cleaned Monday.com datasets using Pandas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from services.data_cleaning_service import (
    clean_deals,
    clean_work_orders,
    fill_missing_values,
    normalize_dates,
    normalize_numbers,
    normalize_status,
)
from services.monday_service import get_deals, get_work_orders
from utils.logger import get_logger

# Initialize logger for Business Intelligence service operations
logger = get_logger("business_intelligence_service")


def _get_cleaned_deals_df() -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Helper function to fetch raw deals, clean them, and convert them to a Pandas DataFrame.

    Returns:
        tuple: (pd.DataFrame of deals, cleaned deals dict response)
    """
    raw_deals_res = get_deals()
    clean_deals_res = clean_deals(raw_deals_res)

    if not clean_deals_res.get("success") or not clean_deals_res.get("deals"):
        logger.warning("No deals data available for Pandas processing.")
        return pd.DataFrame(), clean_deals_res

    deals_list = clean_deals_res.get("deals", [])
    
    # Flatten items into records suitable for Pandas DataFrame
    records = []
    for item in deals_list:
        rec = {
            "id": item.get("id"),
            "name": item.get("name"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "status": item.get("status"),
            "deal_amount": item.get("deal_amount"),
            "board_id": item.get("board_id"),
            "board_name": item.get("board_name"),
        }
        # Extract column values into record attributes
        cols = item.get("columns", {})
        for col_key, col_val in cols.items():
            if isinstance(col_val, dict):
                rec[f"col_{col_key}"] = col_val.get("normalized") or col_val.get("text")

        records.append(rec)

    df = pd.DataFrame(records)
    return df, clean_deals_res


def _get_cleaned_work_orders_df() -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Helper function to fetch raw work orders, clean them, and convert them to a Pandas DataFrame.

    Returns:
        tuple: (pd.DataFrame of work orders, cleaned work orders dict response)
    """
    raw_wo_res = get_work_orders()
    clean_wo_res = clean_work_orders(raw_wo_res)

    if not clean_wo_res.get("success") or not clean_wo_res.get("work_orders"):
        logger.warning("No work orders data available for Pandas processing.")
        return pd.DataFrame(), clean_wo_res

    wo_list = clean_wo_res.get("work_orders", [])

    records = []
    for item in wo_list:
        rec = {
            "id": item.get("id"),
            "name": item.get("name"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "status": item.get("status"),
            "board_id": item.get("board_id"),
            "board_name": item.get("board_name"),
        }
        cols = item.get("columns", {})
        for col_key, col_val in cols.items():
            if isinstance(col_val, dict):
                rec[f"col_{col_key}"] = col_val.get("normalized") or col_val.get("text")

        records.append(rec)

    df = pd.DataFrame(records)
    return df, clean_wo_res


def get_pipeline_summary() -> Dict[str, Any]:
    """
    Calculates total number of deals, total pipeline monetary value, and average deal value.

    Returns:
        dict: Summary containing total_deals, total_pipeline_value, average_deal_value.
    """
    logger.info("Computing sales pipeline summary...")
    df, clean_res = _get_cleaned_deals_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {
            "success": True,
            "total_deals": 0,
            "total_pipeline_value": 0.0,
            "average_deal_value": 0.0,
            "message": "Sales pipeline contains 0 deals.",
        }

    total_deals = len(df)

    # Search for monetary deal value column if deal_amount is missing/incomplete
    value_col = None
    if "deal_amount" in df.columns and df["deal_amount"].notna().sum() > 0:
        value_series = pd.to_numeric(df["deal_amount"], errors="coerce").fillna(0)
    else:
        # Fallback: look for numeric columns containing value/amount
        numeric_cols = [c for c in df.columns if c.startswith("col_")]
        found_series = None
        for c in numeric_cols:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().sum() > 0:
                found_series = s.fillna(0)
                break
        value_series = found_series if found_series is not None else pd.Series([0] * total_deals)

    total_pipeline_value = float(value_series.sum())
    average_deal_value = float(value_series.mean()) if total_deals > 0 else 0.0

    logger.info(f"Pipeline Summary computed: {total_deals} deals, total value: {total_pipeline_value:.2f}")

    return {
        "success": True,
        "total_deals": total_deals,
        "total_pipeline_value": round(total_pipeline_value, 2),
        "average_deal_value": round(average_deal_value, 2),
    }


def get_deals_by_stage() -> Dict[str, Any]:
    """
    Groups deals by stage/status and computes the count distribution per stage.

    Returns:
        dict: Breakdown of deals count per sales stage.
    """
    logger.info("Grouping deals by stage...")
    df, clean_res = _get_cleaned_deals_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {"success": True, "total_deals": 0, "by_stage": {}}

    # Find stage column (search col_ text columns with stage/status keywords)
    stage_col = None
    for col in df.columns:
        if col.startswith("col_"):
            sample_vals = df[col].dropna().astype(str).tolist()
            if any("lead" in v.lower() or "qualif" in v.lower() or "proposal" in v.lower() or "close" in v.lower() for v in sample_vals[:10]):
                stage_col = col
                break

    if not stage_col:
        stage_col = "status" if "status" in df.columns else df.columns[0]

    # Handle missing stage values
    df[stage_col] = df[stage_col].fillna("Unassigned").astype(str).str.strip()
    stage_counts = df[stage_col].value_counts().to_dict()

    formatted_stages = [{"stage": k, "count": int(v)} for k, v in stage_counts.items()]

    logger.info(f"Grouped deals across {len(stage_counts)} stage(s).")
    return {
        "success": True,
        "total_deals": len(df),
        "by_stage": stage_counts,
        "stages_list": formatted_stages,
    }


def get_execution_status_summary() -> Dict[str, Any]:
    """
    Groups work orders by execution status and returns the distribution count.

    Returns:
        dict: Breakdown of work orders per execution status.
    """
    logger.info("Computing execution status summary for work orders...")
    df, clean_res = _get_cleaned_work_orders_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {"success": True, "total_work_orders": 0, "status_summary": {}}

    # Identify execution status column (e.g. col_text_mm5n2f02 or status)
    status_col = "status"
    for col in df.columns:
        if col.startswith("col_"):
            sample_vals = df[col].dropna().astype(str).tolist()
            if any(v.lower() in ("completed", "in progress", "pending", "update required", "stuck") for v in sample_vals[:10]):
                status_col = col
                break

    df[status_col] = df[status_col].fillna("Unknown").astype(str).str.strip()
    status_counts = df[status_col].value_counts().to_dict()

    formatted_summary = [{"status": k, "count": int(v)} for k, v in status_counts.items()]

    logger.info(f"Execution status summary computed: {len(df)} total work orders across {len(status_counts)} statuses.")
    return {
        "success": True,
        "total_work_orders": len(df),
        "status_summary": status_counts,
        "status_list": formatted_summary,
    }


def get_overdue_work_orders() -> Dict[str, Any]:
    """
    Identifies work orders where target/probable end date is before today and execution status is not completed.

    Returns:
        dict: List of overdue work orders with calculated days overdue.
    """
    logger.info("Checking for overdue work orders...")
    df, clean_res = _get_cleaned_work_orders_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {"success": True, "count": 0, "overdue_work_orders": []}

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Locate date column for probable end date / target date
    date_col = None
    for col in df.columns:
        if col.startswith("col_"):
            sample_dates = df[col].dropna().astype(str).tolist()
            if any("GMT" in d or "20" in d for d in sample_dates[:10]):
                date_col = col
                break

    if not date_col and "updated_at" in df.columns:
        date_col = "updated_at"

    # Identify execution status column
    status_col = "status"
    for col in df.columns:
        if col.startswith("col_"):
            sample_vals = df[col].dropna().astype(str).tolist()
            if any(v.lower() in ("completed", "in progress", "pending") for v in sample_vals[:10]):
                status_col = col
                break

    overdue_items = []
    if date_col and date_col in df.columns:
        for _, row in df.iterrows():
            raw_date = row.get(date_col)
            normalized_d = normalize_dates(raw_date)
            status_val = str(row.get(status_col, "")).strip()

            # Check if status is incomplete (not Completed/Done)
            if status_val.lower() not in ("completed", "done", "closed"):
                if normalized_d and normalized_d < today_str:
                    try:
                        dt_target = datetime.strptime(normalized_d, "%Y-%m-%d")
                        dt_today = datetime.strptime(today_str, "%Y-%m-%d")
                        days_overdue = (dt_today - dt_target).days
                    except Exception:
                        days_overdue = 0

                    overdue_items.append({
                        "id": str(row.get("id")),
                        "name": str(row.get("name")),
                        "target_date": normalized_d,
                        "status": status_val,
                        "days_overdue": days_overdue,
                    })

    logger.info(f"Identified {len(overdue_items)} overdue work order(s).")
    return {
        "success": True,
        "count": len(overdue_items),
        "overdue_work_orders": overdue_items,
    }


def get_top_customers(limit: int = 10) -> Dict[str, Any]:
    """
    Ranks customers by the highest number of work orders.

    Args:
        limit (int): Number of top customers to return (default: 10).

    Returns:
        dict: List of top customer objects with work order counts.
    """
    logger.info(f"Computing top {limit} customers by work order volume...")
    df, clean_res = _get_cleaned_work_orders_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {"success": True, "count": 0, "top_customers": []}

    # Locate customer/company column (e.g. col_text_mm5neacp or columns matching WOCOMPANY / COMPANY)
    customer_col = None
    for col in df.columns:
        if col.startswith("col_"):
            sample_vals = df[col].dropna().astype(str).tolist()
            if any("company" in v.lower() or "wocompany" in v.lower() for v in sample_vals[:10]):
                customer_col = col
                break

    if not customer_col:
        customer_col = "name"

    df[customer_col] = df[customer_col].fillna("Unknown Customer").astype(str).str.strip()
    cust_counts = df[customer_col].value_counts().head(limit)

    top_list = [
        {"customer": customer_name, "work_order_count": int(count)}
        for customer_name, count in cust_counts.items()
    ]

    logger.info(f"Successfully retrieved top {len(top_list)} customer(s).")
    return {
        "success": True,
        "limit": limit,
        "count": len(top_list),
        "top_customers": top_list,
    }


def get_pending_invoices() -> Dict[str, Any]:
    """
    Lists work order items that have pending invoices or uncollected payment balances.

    Returns:
        dict: List of pending invoice records.
    """
    logger.info("Extracting pending invoices...")
    df, clean_res = _get_cleaned_work_orders_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {"success": True, "count": 0, "pending_invoices": []}

    # Locate invoice number and numeric amount columns
    inv_num_col = None
    inv_amt_col = None
    coll_amt_col = None

    for col in df.columns:
        if col.startswith("col_"):
            sample_vals = df[col].dropna().astype(str).tolist()
            if not inv_num_col and any("sdpl" in v.lower() or "fy" in v.lower() or "inv" in v.lower() for v in sample_vals[:10]):
                inv_num_col = col

    # Identify numeric columns for invoiced amount vs collected amount
    num_cols = []
    for col in df.columns:
        if col.startswith("col_"):
            numeric_s = pd.to_numeric(df[col], errors="coerce")
            if numeric_s.notna().sum() > 0:
                num_cols.append(col)

    if len(num_cols) >= 2:
        inv_amt_col = num_cols[0]
        coll_amt_col = num_cols[1]
    elif len(num_cols) == 1:
        inv_amt_col = num_cols[0]

    pending_list = []
    for _, row in df.iterrows():
        inv_number = str(row.get(inv_num_col, "")).strip() if inv_num_col else "N/A"
        invoiced_val = normalize_numbers(row.get(inv_amt_col)) if inv_amt_col else 0.0
        collected_val = normalize_numbers(row.get(coll_amt_col)) if coll_amt_col else 0.0

        invoiced_amt = float(invoiced_val) if isinstance(invoiced_val, (int, float)) else 0.0
        collected_amt = float(collected_val) if isinstance(collected_val, (int, float)) else 0.0
        balance_due = max(0.0, invoiced_amt - collected_amt)

        # Include if balance is pending or invoice number exists and incomplete
        if balance_due > 0 or (inv_number and inv_number != "N/A" and collected_amt < invoiced_amt):
            pending_list.append({
                "id": str(row.get("id")),
                "name": str(row.get("name")),
                "invoice_number": inv_number if inv_number != "" else "N/A",
                "invoiced_amount": round(invoiced_amt, 2),
                "collected_amount": round(collected_amt, 2),
                "pending_amount": round(balance_due, 2),
                "status": str(row.get("status", "Pending")),
            })

    logger.info(f"Found {len(pending_list)} pending invoice record(s).")
    return {
        "success": True,
        "count": len(pending_list),
        "pending_invoices": pending_list,
    }


def get_revenue_summary() -> Dict[str, Any]:
    """
    Computes revenue summary including total invoiced amount, total collected amount, and pending collection balance.

    Returns:
        dict: Summary containing total_invoiced_amount, total_collected_amount, pending_collection_amount.
    """
    logger.info("Computing overall revenue summary...")
    df, clean_res = _get_cleaned_work_orders_df()

    if not clean_res.get("success"):
        return clean_res

    if df.empty:
        return {
            "success": True,
            "total_invoiced_amount": 0.0,
            "total_collected_amount": 0.0,
            "pending_collection_amount": 0.0,
        }

    # Find numeric columns representing invoiced vs collected revenue
    num_cols = []
    for col in df.columns:
        if col.startswith("col_"):
            numeric_s = pd.to_numeric(df[col], errors="coerce")
            if numeric_s.notna().sum() > 0:
                num_cols.append((col, numeric_s.sum()))

    # Sort numeric columns by magnitude of sum
    num_cols.sort(key=lambda x: x[1], reverse=True)

    invoiced_sum = 0.0
    collected_sum = 0.0

    if len(num_cols) >= 2:
        invoiced_sum = float(pd.to_numeric(df[num_cols[0][0]], errors="coerce").fillna(0).sum())
        collected_sum = float(pd.to_numeric(df[num_cols[1][0]], errors="coerce").fillna(0).sum())
    elif len(num_cols) == 1:
        invoiced_sum = float(pd.to_numeric(df[num_cols[0][0]], errors="coerce").fillna(0).sum())

    pending_sum = max(0.0, invoiced_sum - collected_sum)

    logger.info(f"Revenue Summary computed: Invoiced: ${invoiced_sum:.2f}, Collected: ${collected_sum:.2f}, Pending: ${pending_sum:.2f}")

    return {
        "success": True,
        "total_invoiced_amount": round(invoiced_sum, 2),
        "total_collected_amount": round(collected_sum, 2),
        "pending_collection_amount": round(pending_sum, 2),
    }
