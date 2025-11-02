"""
Accounting Module - Retrieve Schwab account information
"""

from tabulate import tabulate
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
import requests

from client.schwab_client import SchwabClient


class Accounting:
    def __init__(self):
        self.client = SchwabClient()

    def get_account_numbers(self):
        """
        Get account numbers and their encrypted hash values.

        Returns:
            list: List of plain account numbers (for display purposes)

        Note: This method prints the full response which includes both
        accountNumber and hashValue. Use get_account_info() to get
        the structured data with hash values.
        """
        url = f"{self.client.base_url}/trader/v1/accounts/accountNumbers"
        headers = self.client.get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(json.dumps(data, indent=4))  # Visualize full JSON

        # Extract all account numbers safely
        account_numbers = [
            acc["accountNumber"]
            for acc in data
            if "accountNumber" in acc
        ]

        return account_numbers

    def get_account_info(self):
        """
        Get detailed account information including encrypted hash values.

        Returns:
            list: List of dictionaries with account info:
                [
                    {
                        "accountNumber": "123456789",  # Plain account number
                        "hashValue": "ABC123XYZ"       # Encrypted ID for API calls
                    },
                    ...
                ]

        Usage:
            account_info = accounting.get_account_info()
            encrypted_id = account_info[0]["hashValue"]  # Use this for orders/transactions
            plain_number = account_info[0]["accountNumber"]  # Use this for display
        """
        url = f"{self.client.base_url}/trader/v1/accounts/accountNumbers"
        headers = self.client.get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def get_encrypted_account_id(self, account_number=None):
        """
        Get the encrypted account ID (hashValue) for a specific account.

        Args:
            account_number (str, optional): Plain account number. 
                If None, returns the first account's hash value.

        Returns:
            str: Encrypted account ID (hashValue) to use in API calls

        Raises:
            ValueError: If account_number is provided but not found
        """
        account_info = self.get_account_info()

        if account_number is None:
            # Return first account's hash
            if account_info:
                return account_info[0]["hashValue"]
            raise ValueError("No accounts found")

        # Find specific account
        for acc in account_info:
            if acc["accountNumber"] == str(account_number):
                return acc["hashValue"]

        raise ValueError(f"Account number {account_number} not found")

    def get_all_encrypted_ids(self):
        """
        Get all encrypted account IDs mapped to their plain account numbers.

        Returns:
            dict: Dictionary mapping plain account numbers to encrypted IDs
                {
                    "123456789": "ABC123XYZ",
                    "987654321": "XYZ789ABC"
                }
        """
        account_info = self.get_account_info()
        return {
            acc["accountNumber"]: acc["hashValue"]
            for acc in account_info
        }