from tabulate import tabulate
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
import json
import requests

from client.schwab_client import SchwabClient

class Accounting:
    def __init__(self):

        self.client = SchwabClient()

    def get_account_numbers(self):
        import requests
        url = f"{self.client.base_url}/trader/v1/accounts"
        headers = self.client.get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(json.dumps(data, indent=4))  # Optional: visualize full JSON

        # Extract all account numbers safely
        account_numbers = [
            acc["securitiesAccount"]["accountNumber"]
            for acc in data
            if "securitiesAccount" in acc and "accountNumber" in acc["securitiesAccount"]
        ]

        return account_numbers



