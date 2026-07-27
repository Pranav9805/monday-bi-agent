"""
Monday.com GraphQL API Client Service.

Provides reusable functions to query Monday.com boards, items, deals, and work orders.
Handles authentication via environment variables, cursor pagination, network errors,
and GraphQL error responses, returning clean Python dictionaries.
"""

import os
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv

from utils.logger import get_logger

# Initialize logger for Monday service operations
logger = get_logger("monday_service")

# Load environment variables from .env file
load_dotenv()


class MondayService:
    """
    Service class handling interactions with Monday.com GraphQL API v2.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        deals_board_id: Optional[str] = None,
        work_orders_board_id: Optional[str] = None,
    ):
        """
        Initialize MondayService with API credentials and specific board IDs.

        Reads MONDAY_API_KEY, MONDAY_API_URL, DEALS_BOARD_ID, and WORK_ORDERS_BOARD_ID
        from environment variables if not passed explicitly.
        """
        self.api_key = api_key or os.getenv("MONDAY_API_KEY")
        self.api_url = api_url or os.getenv("MONDAY_API_URL", "https://api.monday.com/v2")
        self.deals_board_id = deals_board_id or os.getenv("DEALS_BOARD_ID")
        self.work_orders_board_id = work_orders_board_id or os.getenv("WORK_ORDERS_BOARD_ID")

        if not self.api_key or self.api_key == "your_monday_api_key_here":
            logger.warning("MONDAY_API_KEY is missing or unconfigured in environment variables.")

    def _validate_board_id(self, board_id: Optional[str], env_var_name: str) -> Optional[str]:
        """
        Validates that a board ID is provided, non-empty, and not a placeholder string.

        Args:
            board_id (str, optional): Board ID value to validate.
            env_var_name (str): Name of environment variable for error reporting.

        Returns:
            str or None: Validated board ID string, or None if missing/invalid.
        """
        if not board_id or not str(board_id).strip():
            logger.error(f"Board ID validation error: {env_var_name} is missing or empty.")
            return None

        clean_id = str(board_id).strip()
        if clean_id.startswith("your_") or clean_id.upper() == "PLACEHOLDER":
            logger.error(f"Board ID validation error: {env_var_name} is set to placeholder '{clean_id}'.")
            return None

        return clean_id

    def _get_headers(self) -> Dict[str, str]:
        """
        Build authorization and content-type headers required for Monday.com GraphQL API requests.
        """
        return {
            "Authorization": self.api_key or "",
            "Content-Type": "application/json",
            "API-Version": "2024-01",
        }

    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a GraphQL query against the Monday.com API.

        Handles network timeouts, connection errors, HTTP status errors, and GraphQL payload errors.

        Args:
            query (str): The GraphQL query string.
            variables (dict, optional): Variables for parameterized GraphQL query.

        Returns:
            dict: Parsed response dictionary containing either successful data or detailed error info.
        """
        # Validate presence of API key before dispatching network request
        if not self.api_key or self.api_key == "your_monday_api_key_here":
            logger.error("API Key validation error: MONDAY_API_KEY is missing or invalid.")
            return {
                "success": False,
                "error": "Invalid or missing API key. Please configure MONDAY_API_KEY in .env file.",
            }

        headers = self._get_headers()
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            logger.debug(f"Dispatching GraphQL query to endpoint: {self.api_url}")
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)

            # Handle 401 Unauthorized invalid API key status code
            if response.status_code == 401:
                logger.error("Authentication failure: Invalid Monday.com API Key (HTTP 401).")
                return {
                    "success": False,
                    "error": "Authentication failed. Invalid Monday.com API key (HTTP 401).",
                }

            response.raise_for_status()
            data = response.json()

            # Handle GraphQL level errors returned inside a 200 OK HTTP payload
            if "errors" in data and data["errors"]:
                error_messages = [err.get("message", "Unknown GraphQL error") for err in data["errors"]]
                logger.error(f"Monday GraphQL API error response: {error_messages}")
                return {
                    "success": False,
                    "error": f"GraphQL API Error: {'; '.join(error_messages)}",
                    "raw_errors": data["errors"],
                }

            return {"success": True, "data": data.get("data", {})}

        except requests.exceptions.Timeout:
            logger.error("Network error: Request to Monday.com API timed out after 30 seconds.")
            return {"success": False, "error": "Request timed out while connecting to Monday.com API."}

        except requests.exceptions.ConnectionError:
            logger.error("Network error: Unable to connect to Monday.com API server.")
            return {"success": False, "error": "Connection error while reaching Monday.com API server."}

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP Error occurred during API call: {http_err}")
            return {"success": False, "error": f"HTTP Error: {str(http_err)}"}

        except Exception as e:
            logger.error(f"Unexpected error executing GraphQL query: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests the connection to Monday.com API by querying current user details ('me').

        Returns:
            dict: Standardized response dictionary containing user details or failure explanation.
        """
        logger.info("Testing connection to Monday.com API...")
        query = """
        query {
            me {
                id
                name
                email
            }
        }
        """
        res = self.execute_query(query)
        if res.get("success"):
            user_data = res.get("data", {}).get("me", {})
            logger.info(f"Successfully authenticated as User: {user_data.get('name')} ({user_data.get('email')})")
            return {
                "success": True,
                "user": user_data,
                "message": f"Connected successfully as {user_data.get('name')}",
            }
        return res

    def get_boards(self, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieves all accessible boards from the Monday.com workspace.

        Args:
            limit (int): Maximum number of boards to fetch (default: 100).

        Returns:
            dict: Standardized dictionary containing list of clean board dictionaries.
        """
        logger.info(f"Fetching boards list from Monday workspace (limit: {limit})...")
        query = """
        query ($limit: Int) {
            boards (limit: $limit) {
                id
                name
                state
                board_kind
                workspace {
                    id
                    name
                }
            }
        }
        """
        res = self.execute_query(query, variables={"limit": limit})
        if not res.get("success"):
            return res

        boards_raw = res.get("data", {}).get("boards", [])
        clean_boards = [
            {
                "id": str(b.get("id")),
                "name": b.get("name"),
                "state": b.get("state"),
                "kind": b.get("board_kind"),
                "workspace_id": b.get("workspace", {}).get("id") if b.get("workspace") else None,
                "workspace_name": b.get("workspace", {}).get("name") if b.get("workspace") else None,
            }
            for b in boards_raw
        ]

        logger.info(f"Successfully retrieved {len(clean_boards)} board(s).")
        return {"success": True, "count": len(clean_boards), "boards": clean_boards}

    def get_board_items(self, board_id: str, page_limit: int = 500) -> Dict[str, Any]:
        """
        Fetches all items from a specified board using cursor-based pagination.

        Args:
            board_id (str): The ID of the board to query.
            page_limit (int): Number of items per cursor page (default: 500).

        Returns:
            dict: Clean Python dictionary with board info and all parsed item objects.
        """
        logger.info(f"Fetching items for board_id='{board_id}'...")
        all_raw_items = []
        cursor = None

        # Fetch initial page and get initial items_page cursor
        initial_query = """
        query ($board_ids: [ID!], $limit: Int) {
            boards (ids: $board_ids) {
                id
                name
                items_page (limit: $limit) {
                    cursor
                    items {
                        id
                        name
                        created_at
                        updated_at
                        column_values {
                            id
                            text
                            value
                            type
                        }
                    }
                }
            }
        }
        """
        try:
            parsed_board_id = int(board_id) if str(board_id).isdigit() else board_id
        except ValueError:
            parsed_board_id = board_id

        res = self.execute_query(initial_query, variables={"board_ids": [parsed_board_id], "limit": page_limit})
        if not res.get("success"):
            return res

        boards_data = res.get("data", {}).get("boards", [])
        if not boards_data:
            logger.warning(f"No board found for ID: {board_id}")
            return {"success": False, "error": f"Board with ID {board_id} not found."}

        board_info = boards_data[0]
        items_page = board_info.get("items_page", {})
        cursor = items_page.get("cursor")
        raw_items = items_page.get("items", [])
        all_raw_items.extend(raw_items)

        # Pagination loop: fetch next pages as long as a cursor exists
        next_page_query = """
        query ($limit: Int, $cursor: String!) {
            next_items_page (limit: $limit, cursor: $cursor) {
                cursor
                items {
                    id
                    name
                    created_at
                    updated_at
                    column_values {
                        id
                        text
                        value
                        type
                    }
                }
            }
        }
        """
        page_count = 1
        while cursor:
            page_count += 1
            logger.info(f"Fetching page {page_count} for board {board_id} via cursor...")
            page_res = self.execute_query(next_page_query, variables={"limit": page_limit, "cursor": cursor})

            if not page_res.get("success"):
                logger.error(f"Error fetching page {page_count}: {page_res.get('error')}")
                break

            next_page_data = page_res.get("data", {}).get("next_items_page", {})
            cursor = next_page_data.get("cursor")
            page_items = next_page_data.get("items", [])

            if not page_items:
                break

            all_raw_items.extend(page_items)

        # Parse raw items into clean Python dictionaries
        clean_items = []
        for item in all_raw_items:
            columns_dict = {}
            for col in item.get("column_values", []):
                col_id = col.get("id")
                columns_dict[col_id] = {
                    "text": col.get("text"),
                    "value": col.get("value"),
                    "type": col.get("type"),
                }

            clean_items.append({
                "id": str(item.get("id")),
                "name": item.get("name"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "columns": columns_dict,
            })

        logger.info(f"Successfully retrieved {len(clean_items)} items across {page_count} page(s) for board {board_id}.")
        return {
            "success": True,
            "board_id": str(board_info.get("id")),
            "board_name": board_info.get("name"),
            "total_items": len(clean_items),
            "items": clean_items,
        }

    def get_deals(self) -> Dict[str, Any]:
        """
        Retrieves deal items directly using DEALS_BOARD_ID environment variable.

        Returns:
            dict: Clean Python dictionary containing deal items or an error explanation if ID is missing.
        """
        logger.info("Fetching deals directly using DEALS_BOARD_ID...")
        valid_id = self._validate_board_id(self.deals_board_id, "DEALS_BOARD_ID")
        if not valid_id:
            return {
                "success": False,
                "error": "DEALS_BOARD_ID environment variable is missing or unconfigured in .env file.",
                "deals": [],
            }

        res = self.get_board_items(valid_id)
        if not res.get("success"):
            return res

        items = res.get("items", [])
        return {
            "success": True,
            "board_id": res.get("board_id"),
            "board_name": res.get("board_name"),
            "count": len(items),
            "deals": items,
        }

    def get_work_orders(self) -> Dict[str, Any]:
        """
        Retrieves work order items directly using WORK_ORDERS_BOARD_ID environment variable.

        Returns:
            dict: Clean Python dictionary containing work order items or an error explanation if ID is missing.
        """
        logger.info("Fetching work orders directly using WORK_ORDERS_BOARD_ID...")
        valid_id = self._validate_board_id(self.work_orders_board_id, "WORK_ORDERS_BOARD_ID")
        if not valid_id:
            return {
                "success": False,
                "error": "WORK_ORDERS_BOARD_ID environment variable is missing or unconfigured in .env file.",
                "work_orders": [],
            }

        res = self.get_board_items(valid_id)
        if not res.get("success"):
            return res

        items = res.get("items", [])
        return {
            "success": True,
            "board_id": res.get("board_id"),
            "board_name": res.get("board_name"),
            "count": len(items),
            "work_orders": items,
        }


# Global instance of MondayService for standalone module-level function calls
_default_service = MondayService()


def test_connection() -> Dict[str, Any]:
    """Reusable function to test Monday API connection."""
    return _default_service.test_connection()


def get_boards(limit: int = 100) -> Dict[str, Any]:
    """Reusable function to get workspace boards."""
    return _default_service.get_boards(limit=limit)


def get_board_items(board_id: str) -> Dict[str, Any]:
    """Reusable function to get items for a board."""
    return _default_service.get_board_items(board_id)


def get_deals() -> Dict[str, Any]:
    """Reusable function to get deal records."""
    return _default_service.get_deals()


def get_work_orders() -> Dict[str, Any]:
    """Reusable function to get work order items."""
    return _default_service.get_work_orders()
