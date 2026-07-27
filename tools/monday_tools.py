"""
LangChain Tools for Monday.com Business Intelligence Agent.

Exposes Business Intelligence service functions as LangChain tools decorated with @tool.
Each tool fetches fresh data from Monday.com, cleans it via data_cleaning_service,
computes metrics via business_intelligence_service, and returns clean JSON-serializable dictionaries.
"""

from typing import Any, Dict, Optional
from langchain_core.tools import tool

from services import business_intelligence_service as bi_service
from utils.logger import get_logger

# Initialize logger for Monday tools
logger = get_logger("monday_tools")


@tool
def get_pipeline_summary() -> Dict[str, Any]:
    """
    Fetches the total sales pipeline summary from Monday.com deals board.

    Use this tool when the user asks about the overall sales pipeline, total number of deals,
    total pipeline value (in currency), or the average deal value.

    Returns:
        dict: Standardized dictionary containing total_deals, total_pipeline_value, and average_deal_value.
    """
    logger.info("Executing LangChain tool: get_pipeline_summary")
    try:
        result = bi_service.get_pipeline_summary()
        return result
    except Exception as e:
        logger.error(f"Error executing get_pipeline_summary tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_deals_by_stage() -> Dict[str, Any]:
    """
    Retrieves the distribution of sales deals grouped by sales pipeline stage.

    Use this tool when the user asks for a breakdown of deals by stage, phase, or status.

    Returns:
        dict: Standardized dictionary containing total_deals, by_stage dictionary, and stages_list.
    """
    logger.info("Executing LangChain tool: get_deals_by_stage")
    try:
        result = bi_service.get_deals_by_stage()
        return result
    except Exception as e:
        logger.error(f"Error executing get_deals_by_stage tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_execution_status_summary() -> Dict[str, Any]:
    """
    Retrieves work orders execution status summary from Monday.com work orders board.

    Use this tool when the user asks about project execution status, work order progress,
    or count of completed vs ongoing vs pending work orders.

    Returns:
        dict: Standardized dictionary containing total_work_orders and status_summary.
    """
    logger.info("Executing LangChain tool: get_execution_status_summary")
    try:
        result = bi_service.get_execution_status_summary()
        return result
    except Exception as e:
        logger.error(f"Error executing get_execution_status_summary tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_overdue_work_orders() -> Dict[str, Any]:
    """
    Retrieves all overdue work orders whose target date is before today and status is incomplete.

    Use this tool when the user asks for overdue work orders, delayed projects, or pending deadlines.

    Returns:
        dict: Standardized dictionary containing count of overdue work orders and list of overdue item details.
    """
    logger.info("Executing LangChain tool: get_overdue_work_orders")
    try:
        result = bi_service.get_overdue_work_orders()
        return result
    except Exception as e:
        logger.error(f"Error executing get_overdue_work_orders tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_top_customers(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieves the top customers ranked by their total number of work orders.

    Args:
        limit (int): Maximum number of top customers to return (default: 10).

    Use this tool when the user asks about key clients, top customers, or companies with the highest work order volume.

    Returns:
        dict: Standardized dictionary containing top_customers list with work order counts.
    """
    logger.info(f"Executing LangChain tool: get_top_customers (limit={limit})")
    try:
        result = bi_service.get_top_customers(limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error executing get_top_customers tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_pending_invoices() -> Dict[str, Any]:
    """
    Retrieves work order items that have pending invoices or uncollected payment balances.

    Use this tool when the user asks about pending invoices, unpaid items, or outstanding payments.

    Returns:
        dict: Standardized dictionary containing count and list of pending invoice items.
    """
    logger.info("Executing LangChain tool: get_pending_invoices")
    try:
        result = bi_service.get_pending_invoices()
        return result
    except Exception as e:
        logger.error(f"Error executing get_pending_invoices tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


@tool
def get_revenue_summary() -> Dict[str, Any]:
    """
    Retrieves overall revenue and collection summary across Monday.com work orders.

    Use this tool when the user asks about financial performance, total invoiced amount,
    total collected revenue, or pending collection balances.

    Returns:
        dict: Standardized dictionary containing total_invoiced_amount, total_collected_amount, and pending_collection_amount.
    """
    logger.info("Executing LangChain tool: get_revenue_summary")
    try:
        result = bi_service.get_revenue_summary()
        return result
    except Exception as e:
        logger.error(f"Error executing get_revenue_summary tool: {str(e)}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


# List of all available BI tools for LangChain Agent registration
ALL_BI_TOOLS = [
    get_pipeline_summary,
    get_deals_by_stage,
    get_execution_status_summary,
    get_overdue_work_orders,
    get_top_customers,
    get_pending_invoices,
    get_revenue_summary,
]
