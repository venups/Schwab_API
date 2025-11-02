###################################################

from dotenv import load_dotenv
from pathlib import Path


###################################################

from client.schwab_client import SchwabClient
from src.functions.accounting import Accounting

###################################################

if __name__ == "__main__":

    client = SchwabClient()
    account = Accounting()

    client.handle_authentication(authenticate=False)

    account_number = account.get_account_numbers()
    print(account_number[0])





