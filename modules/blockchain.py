import hashlib


class Transaction:
    def __init__(self, payer:int, payee:int, amount:float, timestamp:float) -> None:
        self.payer = payer
        self.payee = payee
        self.amount = amount
        self.timestamp = timestamp
        self.id = hashlib.sha256(f"{payer}-{payee}-{amount}-{timestamp}".encode())