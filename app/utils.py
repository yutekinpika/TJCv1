import os
import json
from datetime import datetime

TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "transactions.json")

def load_transactions():
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    with open(TRANSACTIONS_FILE, "r") as f:
        return json.load(f)

def save_transaction(tx):
    txs = load_transactions()
    txs.append(tx)
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(txs, f, indent=2)
