"""
Data Cleaning and Normalization Service.

Provides reusable functions to sanitize, format, and normalize raw Monday.com data,
converting date formats, parsing numeric values, standardizing status strings,
handling missing values, and preserving raw data for auditability.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union

from utils.logger import get_logger

# Initialize logger for data cleaning operations
logger = get_logger("data_cleaning_service")


def fill_missing_values(val: Any, default_val: Any = None) -> Any:
    """
    Handles empty strings, null values, and placeholder strings by replacing them with a default value.

    Args:
        val (Any): Input value to check.
        default_val (Any): Fallback value if input is missing/empty (default: None).

    Returns:
        Any: Cleaned value or default_val.
    """
    if val is None:
        return default_val

    if isinstance(val, str):
        trimmed = val.strip()
        if trimmed == "" or trimmed.lower() in ("null", "none", "n/a", "nan", "undefined"):
            return default_val
        return trimmed

    return val


def normalize_dates(val: Any) -> Optional[str]:
    """
    Converts various date formats (ISO string, timestamp, YYYY-MM-DD, etc.) to YYYY-MM-DD string.

    Args:
        val (Any): Input date representation (string or numeric timestamp).

    Returns:
        str or None: Formatted date string 'YYYY-MM-DD' or None if invalid/missing.
    """
    cleaned_val = fill_missing_values(val)
    if cleaned_val is None:
        return None

    val_str = str(cleaned_val).strip()

    # Try common date parsing formats
    date_formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in date_formats:
        try:
            parsed_dt = datetime.strptime(val_str, fmt)
            return parsed_dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Attempt regex extraction of YYYY-MM-DD pattern from string
    match = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", val_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    logger.warning(f"Unable to parse date string: '{val_str}'")
    return val_str


def normalize_numbers(val: Any) -> Optional[Union[int, float]]:
    """
    Converts numeric strings (e.g. '$1,250.50', '100', '12.5%') to float or int.

    Args:
        val (Any): Input value representing a number.

    Returns:
        int, float, or None: Numeric value, or None if conversion fails.
    """
    cleaned_val = fill_missing_values(val)
    if cleaned_val is None:
        return None

    if isinstance(cleaned_val, (int, float)):
        return cleaned_val

    val_str = str(cleaned_val).strip()

    # Remove currency symbols ($ € £), commas, and trailing non-numeric symbols
    cleaned_num_str = re.sub(r"[^\d.-]", "", val_str)

    if not cleaned_num_str or cleaned_num_str == "-":
        return None

    try:
        if "." in cleaned_num_str:
            return float(cleaned_num_str)
        return int(cleaned_num_str)
    except ValueError:
        logger.warning(f"Unable to convert '{val_str}' to a numeric value.")
        return None


def normalize_status(val: Any) -> Optional[str]:
    """
    Standardizes status values into consistent Title Case strings (e.g. 'completed', 'COMPLETE' -> 'Completed').

    Args:
        val (Any): Raw status string.

    Returns:
        str or None: Standardized status string or None if missing.
    """
    cleaned_val = fill_missing_values(val)
    if cleaned_val is None:
        return None

    val_str = str(cleaned_val).strip()

    # Known status mappings dictionary for common Monday status labels
    known_mappings = {
        "done": "Done",
        "completed": "Completed",
        "complete": "Completed",
        "in progress": "In Progress",
        "working on it": "Working on it",
        "pending": "Pending",
        "stuck": "Stuck",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
        "won": "Won",
        "lost": "Lost",
        "open": "Open",
        "closed": "Closed",
    }

    lower_key = val_str.lower()
    if lower_key in known_mappings:
        return known_mappings[lower_key]

    # Default to Title Case format with normalized spacing
    return " ".join(val_str.split()).title()


def _clean_item(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to clean an individual item dictionary from Monday API.

    Args:
        raw_item (dict): Raw item dictionary from Monday service.

    Returns:
        dict: Cleaned item dictionary with raw data preserved under 'raw_data'.
    """
    item_id = fill_missing_values(raw_item.get("id"))
    item_name = fill_missing_values(raw_item.get("name"))
    created_at = normalize_dates(raw_item.get("created_at"))
    updated_at = normalize_dates(raw_item.get("updated_at"))

    columns_clean = {}
    raw_columns = raw_item.get("columns", {})

    status_candidate = None

    for col_id, col_info in raw_columns.items():
        if isinstance(col_info, dict):
            col_text = fill_missing_values(col_info.get("text"))
            col_value = fill_missing_values(col_info.get("value"))
            col_type = col_info.get("type")

            # Try inferring normalized values based on column text
            normalized_val = col_text
            if col_text is not None:
                # Test if numeric
                num_val = normalize_numbers(col_text)
                if num_val is not None and not re.search(r"[a-zA-Z]", col_text):
                    normalized_val = num_val
                # Test if date
                elif re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", col_text):
                    normalized_val = normalize_dates(col_text)

            columns_clean[col_id] = {
                "text": col_text,
                "value": col_value,
                "type": col_type,
                "normalized": normalized_val,
            }

            if col_type in ("status", "color") or "status" in col_id.lower():
                status_candidate = col_text

    cleaned_dict = {
        "id": item_id,
        "name": item_name,
        "created_at": created_at,
        "updated_at": updated_at,
        "status": normalize_status(status_candidate or item_name),
        "columns": columns_clean,
        "board_id": raw_item.get("board_id"),
        "board_name": raw_item.get("board_name"),
        "raw_data": raw_item,  # Preserve original raw data untouched
    }

    return cleaned_dict


def clean_deals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans raw deals data returned by monday_service.get_deals().

    Args:
        data (dict): Raw dictionary returned by get_deals().

    Returns:
        dict: Cleaned deals dictionary with sanitized fields and preserved raw data.
    """
    logger.info("Cleaning deals raw data payload...")
    if not isinstance(data, dict):
        logger.error("Input deals data must be a dictionary.")
        return {"success": False, "error": "Invalid data format. Expected dictionary.", "deals": []}

    if not data.get("success"):
        logger.warning(f"Deals input data indicates unsuccessful response: {data.get('error')}")
        return data

    raw_deals = data.get("deals", [])
    cleaned_deals = []

    for deal in raw_deals:
        cleaned_item = _clean_item(deal)

        # Extract specific deal amount if present in columns
        amount = None
        for col_key, col_val in cleaned_item.get("columns", {}).items():
            col_text = col_val.get("text")
            if col_text and any(keyword in col_key.lower() for keyword in ["amount", "value", "deal_value", "price", "numbers"]):
                amount = normalize_numbers(col_text)
                if amount is not None:
                    break

        cleaned_item["deal_amount"] = amount
        cleaned_deals.append(cleaned_item)

    logger.info(f"Successfully cleaned {len(cleaned_deals)} deal record(s).")
    return {
        "success": True,
        "board_id": data.get("board_id"),
        "board_name": data.get("board_name"),
        "count": len(cleaned_deals),
        "deals": cleaned_deals,
        "raw_response": data,  # Preserve full original response payload
    }


def clean_work_orders(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans raw work orders data returned by monday_service.get_work_orders().

    Args:
        data (dict): Raw dictionary returned by get_work_orders().

    Returns:
        dict: Cleaned work orders dictionary with sanitized fields and preserved raw data.
    """
    logger.info("Cleaning work orders raw data payload...")
    if not isinstance(data, dict):
        logger.error("Input work orders data must be a dictionary.")
        return {"success": False, "error": "Invalid data format. Expected dictionary.", "work_orders": []}

    if not data.get("success"):
        logger.warning(f"Work orders input data indicates unsuccessful response: {data.get('error')}")
        return data

    raw_work_orders = data.get("work_orders", [])
    cleaned_work_orders = []

    for wo in raw_work_orders:
        cleaned_item = _clean_item(wo)
        cleaned_work_orders.append(cleaned_item)

    logger.info(f"Successfully cleaned {len(cleaned_work_orders)} work order record(s).")
    return {
        "success": True,
        "board_id": data.get("board_id"),
        "board_name": data.get("board_name"),
        "count": len(cleaned_work_orders),
        "work_orders": cleaned_work_orders,
        "raw_response": data,  # Preserve full original response payload
    }
