"""
Example usage of the Orders module
Demonstrates how to retrieve and display orders from Schwab accounts
"""

from client.schwab_client import SchwabClient
from src.functions.accounting import Accounting
from src.functions.orders import Orders
import json


def main():

    # Initialize and authenticate
    client = SchwabClient()
    accounting = Accounting()
    orders = Orders()

    client.handle_authentication(authenticate=False)

    # Get account information (includes encrypted IDs)
    print("\n" + "=" * 60)
    print("ACCOUNT INFORMATION")
    print("=" * 60)

    account_info = accounting.get_account_info()

    for acc in account_info:
        print(f"\nAccount Number: {acc['accountNumber']}")
        print(f"Encrypted ID:   {acc['hashValue']}")

    # Use the first account
    first_account = account_info[0]
    plain_number = first_account["accountNumber"]
    encrypted_id = first_account["hashValue"]

    print(f"\n🎯 Using account: {plain_number}")

    # ========================================
    # Example: Get last 30 days of orders
    # ========================================
    print("\n" + "=" * 60)
    print("ORDERS - LAST 30 DAYS")
    print("=" * 60)

    # Method 1: Using encrypted ID directly (faster)
    orders_list = orders.get_orders_by_days(
        account_id=encrypted_id,
        days=30
    )

    # Display as formatted table
    orders.print_orders_table(orders_list)

    # ========================================
    # Example: Get only filled orders
    # ========================================
    print("\n" + "=" * 60)
    print("FILLED ORDERS - LAST 60 DAYS")
    print("=" * 60)

    filled_orders = orders.get_orders_by_days(
        account_id=encrypted_id,
        days=60,
        status="FILLED"
    )

    orders.print_orders_table(filled_orders)

    # ========================================
    # Alternative: Use convenience method with plain account number
    # ========================================
    # This automatically converts plain number to encrypted ID

    # orders_list = orders.get_orders_by_plain_account(
    #     account_number=plain_number,
    #     days=30
    # )


if __name__ == "__main__":
    main()