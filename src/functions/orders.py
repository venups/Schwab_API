"""
Orders Module - Retrieve and manage Schwab account orders
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from tabulate import tabulate
import pandas as pd

from client.schwab_client import SchwabClient


class Orders:
    """
    Handle order-related operations for Schwab accounts.

    Note: Schwab API requires ENCRYPTED account IDs (hashValue) for order endpoints,
    not plain account numbers.
    """

    def __init__(self):
        """Initialize Orders with SchwabClient instance."""
        self.client = SchwabClient()

    def get_orders_by_days(
        self,
        account_id: str,
        days: int = 30,
        max_results: int = 3000,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all orders for a specific account within the last N days.

        Args:
            account_id (str): The ENCRYPTED account ID (hashValue), NOT plain account number.
                Use Accounting.get_encrypted_account_id() to get this value.
            days (int): Number of days back from today to retrieve orders (default: 30, max: 365)
            max_results (int): Maximum number of orders to retrieve (default: 3000)
            status (str, optional): Filter by order status. Available values:
                - AWAITING_PARENT_ORDER, AWAITING_CONDITION, AWAITING_STOP_CONDITION
                - AWAITING_MANUAL_REVIEW, ACCEPTED, AWAITING_UR_OUT
                - PENDING_ACTIVATION, QUEUED, WORKING, REJECTED
                - PENDING_CANCEL, CANCELED, PENDING_REPLACE, REPLACED
                - FILLED, EXPIRED, NEW, AWAITING_RELEASE_TIME
                - PENDING_ACKNOWLEDGEMENT, PENDING_RECALL, UNKNOWN

        Returns:
            List[Dict]: List of order dictionaries

        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If days > 365 (Schwab API limit)

        Example:
            accounting = Accounting()
            orders = Orders()

            # Get encrypted account ID
            encrypted_id = accounting.get_encrypted_account_id()

            # Get orders using encrypted ID
            order_list = orders.get_orders_by_days(encrypted_id, days=30)
        """
        # Validate days parameter
        if days > 365:
            raise ValueError("Days cannot exceed 365 (Schwab API maximum date range is 1 year)")

        # Calculate date range in ISO-8601 format
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        # Format dates as required by Schwab API: yyyy-MM-dd'T'HH:mm:ss.SSSZ
        to_entered_time = to_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        from_entered_time = from_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Build API endpoint - MUST use encrypted account ID
        url = f"{self.client.base_url}/trader/v1/accounts/{account_id}/orders"

        # Build query parameters
        params = {
            "fromEnteredTime": from_entered_time,
            "toEnteredTime": to_entered_time,
            "maxResults": max_results
        }

        # Add status filter if provided
        if status:
            params["status"] = status

        # Get headers with access token
        headers = self.client.get_headers()

        print(f"\n📊 Fetching orders for encrypted account ID: {account_id[:8]}...")
        print(f"   Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')} ({days} days)")
        if status:
            print(f"   Status filter: {status}")

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            orders = response.json()

            print(f"✅ Retrieved {len(orders)} orders")

            return orders

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error fetching orders: {e}")
            print(f"   Response: {e.response.text}")
            if "Invalid account number" in e.response.text:
                print("\n⚠️  ERROR: You must use the ENCRYPTED account ID (hashValue), not plain account number!")
                print("   Fix: Use Accounting.get_encrypted_account_id() to get the correct value.")
            raise
        except Exception as e:
            print(f"❌ Error fetching orders: {e}")
            raise

    def get_orders_by_plain_account(
        self,
        account_number: str,
        days: int = 30,
        max_results: int = 3000,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get orders using a plain account number (convenience method).

        This method automatically converts the plain account number to its
        encrypted ID before making the API call.

        Args:
            account_number (str): Plain account number (e.g., "123456789")
            days (int): Number of days back from today
            max_results (int): Maximum number of orders to retrieve
            status (str, optional): Filter by order status

        Returns:
            List[Dict]: List of order dictionaries
        """
        from src.functions.accounting import Accounting

        accounting = Accounting()
        encrypted_id = accounting.get_encrypted_account_id(account_number)

        return self.get_orders_by_days(
            account_id=encrypted_id,
            days=days,
            max_results=max_results,
            status=status
        )

    def get_all_accounts_orders(
        self,
        days: int = 30,
        max_results: int = 3000,
        status: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get orders for all linked accounts.

        Args:
            days (int): Number of days back from today
            max_results (int): Maximum number of orders per account
            status (str, optional): Filter by order status

        Returns:
            Dict[str, List[Dict]]: Dictionary mapping plain account numbers to their orders
        """
        from src.functions.accounting import Accounting

        accounting = Accounting()
        account_mapping = accounting.get_all_encrypted_ids()

        all_orders = {}

        for plain_number, encrypted_id in account_mapping.items():
            try:
                print(f"\n🔄 Fetching orders for account {plain_number}...")
                orders = self.get_orders_by_days(
                    account_id=encrypted_id,
                    days=days,
                    max_results=max_results,
                    status=status
                )
                all_orders[plain_number] = orders
            except Exception as e:
                print(f"⚠️  Failed to retrieve orders for account {plain_number}: {e}")
                all_orders[plain_number] = []

        return all_orders

    def format_orders_summary(self, orders: List[Dict]) -> pd.DataFrame:
        """
        Format orders into a readable pandas DataFrame summary.

        Args:
            orders (List[Dict]): List of order dictionaries

        Returns:
            pd.DataFrame: Formatted summary of orders
        """
        if not orders:
            return pd.DataFrame()

        summary_data = []

        for order in orders:
            # Extract key order information
            order_id = order.get("orderId", "N/A")
            status = order.get("status", "N/A")
            entered_time = order.get("enteredTime", "N/A")

            # Parse entered time for better readability
            if entered_time != "N/A":
                try:
                    dt = datetime.fromisoformat(entered_time.replace("Z", "+00:00"))
                    entered_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass

            # Extract order leg information (symbol, quantity, instruction)
            order_legs = order.get("orderLegCollection", [])
            if order_legs:
                leg = order_legs[0]  # First leg
                symbol = leg.get("instrument", {}).get("symbol", "N/A")
                quantity = leg.get("quantity", 0)
                instruction = leg.get("instruction", "N/A")
            else:
                symbol = "N/A"
                quantity = 0
                instruction = "N/A"

            order_type = order.get("orderType", "N/A")
            duration = order.get("duration", "N/A")
            price = order.get("price", "N/A")

            summary_data.append({
                "Order ID": order_id,
                "Status": status,
                "Symbol": symbol,
                "Instruction": instruction,
                "Quantity": quantity,
                "Type": order_type,
                "Price": price,
                "Duration": duration,
                "Entered Time": entered_time
            })

        df = pd.DataFrame(summary_data)
        return df

    def print_orders_table(self, orders: List[Dict]) -> None:
        """
        Print orders in a formatted table using tabulate.

        Args:
            orders (List[Dict]): List of order dictionaries
        """
        df = self.format_orders_summary(orders)

        if df.empty:
            print("\n📭 No orders found.")
            return

        print("\n" + "="*120)
        print("ORDERS SUMMARY")
        print("="*120)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print("="*120 + "\n")

    def get_orders_json(
        self,
        account_id: str,
        days: int = 30,
        pretty: bool = True
    ) -> str:
        """
        Get orders as formatted JSON string.

        Args:
            account_id (str): The ENCRYPTED account ID (hashValue)
            days (int): Number of days back from today
            pretty (bool): Whether to format JSON with indentation

        Returns:
            str: JSON string of orders
        """
        orders = self.get_orders_by_days(account_id, days)

        if pretty:
            return json.dumps(orders, indent=4)
        return json.dumps(orders)

    def filter_orders_by_symbol(
        self,
        orders: List[Dict],
        symbol: str
    ) -> List[Dict]:
        """
        Filter orders by stock symbol.

        Args:
            orders (List[Dict]): List of order dictionaries
            symbol (str): Stock symbol to filter by (e.g., 'AAPL', 'SPY')

        Returns:
            List[Dict]: Filtered list of orders
        """
        filtered_orders = []

        for order in orders:
            order_legs = order.get("orderLegCollection", [])
            for leg in order_legs:
                instrument_symbol = leg.get("instrument", {}).get("symbol", "")
                if instrument_symbol.upper() == symbol.upper():
                    filtered_orders.append(order)
                    break  # Only add once per order

        return filtered_orders

    def filter_orders_by_status(
        self,
        orders: List[Dict],
        status: str
    ) -> List[Dict]:
        """
        Filter orders by status.

        Args:
            orders (List[Dict]): List of order dictionaries
            status (str): Status to filter by (e.g., 'FILLED', 'WORKING')

        Returns:
            List[Dict]: Filtered list of orders
        """
        return [
            order for order in orders
            if order.get("status", "").upper() == status.upper()
        ]